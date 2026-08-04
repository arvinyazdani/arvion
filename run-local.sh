#!/usr/bin/env sh
set -eu

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

. .venv/bin/activate
python manage.py migrate
python manage.py seed_initial_data
python manage.py runserver 127.0.0.1:8000
