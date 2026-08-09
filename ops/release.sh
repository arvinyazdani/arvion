#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/srv/arvion}"
ENV_FILE="${ENV_FILE:-$APP_DIR/.env.production}"
set -a
source "$ENV_FILE"
set +a
cd "$APP_DIR"
"$APP_DIR/.venv/bin/python" manage.py check --deploy
"$APP_DIR/.venv/bin/python" manage.py migrate --noinput
"$APP_DIR/.venv/bin/python" manage.py setup_staff_roles
"$APP_DIR/.venv/bin/python" manage.py seed_assessment_banks
"$APP_DIR/.venv/bin/python" manage.py collectstatic --noinput
