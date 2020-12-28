import uuid
from contextlib import contextmanager
from typing import List, Tuple

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel


sql_url = "postgresql://postgres@localhost/pollbits"


psycopg2.extras.register_uuid()
app = FastAPI()


class PollIn(BaseModel):
    text: str
    answers: List[str]


class Answer(BaseModel):
    uuid: uuid.UUID
    text: str
    votes: int


class Poll(BaseModel):
    uuid: uuid.UUID
    text: str
    answers: List[Answer]


class PollSimple(BaseModel):
    uuid: uuid.UUID
    text: str


@contextmanager
def database() -> psycopg2.extensions.cursor:
    try:
        connection = psycopg2.connect(sql_url)
        cursor: psycopg2.extensions.cursor = connection.cursor()
        yield cursor
        connection.commit()
    finally:
        cursor.close()
        connection.close()


@app.post("/polls")
def create_poll(poll: PollIn) -> uuid.UUID:
    with database() as db:
        poll_db = (poll.text,)
        db.execute("INSERT INTO poll (text) VALUES(%s) RETURNING id", poll_db)
        poll_uuid = db.fetchone()[0]
        answers_db = [(poll_uuid, answer) for answer in poll.answers]
        db.executemany(
            "INSERT INTO answer (poll_id, text) VALUES(%s, %s)",
            answers_db,
        )

        return poll_uuid


@app.get("/polls")
def get_polls() -> List[PollSimple]:
    with database() as db:
        db.execute("SELECT poll.id, poll.text FROM poll")
        polls_db = db.fetchall()

    def make_poll(poll_db: Tuple[uuid.UUID, str]):
        poll_uuid, poll_text = poll_db
        return PollSimple(uuid=poll_uuid, text=poll_text)

    polls = [make_poll(poll_db) for poll_db in polls_db]

    return polls


@app.get("/polls/{poll_uuid}")
def get_poll(poll_uuid: uuid.UUID) -> Poll:
    with database() as db:
        db.execute(
            "SELECT poll.id, poll.text, answer.id, answer.text, COUNT(vote.id) FROM poll"
            " LEFT JOIN answer on poll.id = answer.poll_id"
            " LEFT JOIN vote on answer.id = vote.answer_id"
            " WHERE poll.id = %s"
            " GROUP BY poll.id, answer.id",
            (poll_uuid,),
        )
        poll_db = db.fetchall()

    if not poll_db:
        raise HTTPException(404, "Poll not found")

    def make_poll(poll_db: List[Tuple[uuid.UUID, str, uuid.UUID, str, int]]):
        poll_uuid = poll_db[0][0]
        answers = [
            Answer(uuid=answer_uuid, text=text, votes=votes)
            for _, _, answer_uuid, text, votes in poll_db
        ]
        return Poll(uuid=poll_uuid, text=poll_db[0][1], answers=answers)

    poll = make_poll(poll_db)

    return poll


@app.post("/vote/{answer_uuid}", status_code=204, response_class=Response)
def vote(answer_uuid: uuid.UUID) -> None:
    with database() as db:
        db.execute("INSERT INTO vote (answer_id) VALUES(%s)", (answer_uuid,))
