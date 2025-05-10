#!/usr/bin/env bash
set -e

python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py collectstatic --noinput

gunicorn foodgram.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120
