#!/bin/bash

while ! nc -z db 5432; do
  echo "Waiting for database $db..."
  sleep 1
done

sleep 5

rm -rf alembic/versions
mkdir -p alembic/versions
alembic revision --autogenerate -m "First Migration"
alembic upgrade head

uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
