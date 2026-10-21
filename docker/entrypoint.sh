#!/bin/sh
set -e

# Wait for PostgreSQL and bring the schema up to date before serving.
python -m dragon_city migrate

exec gunicorn --config /app/docker/gunicorn.conf.py dragon_city.wsgi:app
