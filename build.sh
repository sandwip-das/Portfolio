#!/usr/bin/env bash

set -o errexit

pip install -r requirements.txt

python manage.py migrate --noinput

python manage.py collectstatic --noinput --clear

# Previous Start command in Render (06 May 2026)
# python manage.py migrate && python manage.py collectstatic --noinput && gunicorn portfolio.wsgi:application --bind 0.0.0.0:$PORT