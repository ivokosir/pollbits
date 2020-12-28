CREATE TABLE poll (
	id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
	text TEXT NOT NULL
);

CREATE TABLE answer (
	id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
	poll_id UUID,
  text TEXT NOT NULL,
  FOREIGN KEY (poll_id)
    REFERENCES poll (id)
      ON DELETE CASCADE
);

CREATE TABLE vote (
  id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  answer_id UUID,
  FOREIGN KEY (answer_id)
    REFERENCES answer (id)
      ON DELETE CASCADE
);
