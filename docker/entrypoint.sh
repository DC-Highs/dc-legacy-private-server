#!/bin/sh
set -e

# Wait for PostgreSQL and bring the schema up to date before serving.
python -m src migrate

exec gunicorn --config /app/docker/gunicorn.conf.py src.wsgi:app
