#! /bin/env sh

dropdb -h localhost -U postgres pollbits --if-exists
createdb -h localhost -U postgres pollbits
psql postgresql://postgres@localhost/pollbits < create_database.sql
