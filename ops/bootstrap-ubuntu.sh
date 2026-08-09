#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/srv/arvion}"
APP_USER="${APP_USER:-arvion}"
ENV_FILE="${ENV_FILE:-$APP_DIR/.env.production}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo APP_DIR=$APP_DIR $0" >&2
  exit 1
fi
if [[ ! -f "$APP_DIR/manage.py" || ! -f "$APP_DIR/requirements.txt" ]]; then
  echo "Project source is missing from $APP_DIR" >&2
  exit 1
fi
if [[ ! -f "$ENV_FILE" ]]; then
  echo "Create $ENV_FILE from .env.example and fill all production secrets first." >&2
  exit 1
fi

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y python3-venv python3-dev build-essential libpq-dev nginx
id "$APP_USER" >/dev/null 2>&1 || useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin "$APP_USER"
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
chmod 600 "$ENV_FILE"

install -m 0644 "$APP_DIR/ops/arvion.service" /etc/systemd/system/arvion.service
install -m 0644 "$APP_DIR/ops/arvion-traffic-cleanup.service" /etc/systemd/system/arvion-traffic-cleanup.service
install -m 0644 "$APP_DIR/ops/arvion-traffic-cleanup.timer" /etc/systemd/system/arvion-traffic-cleanup.timer
install -m 0644 "$APP_DIR/ops/nginx.conf" /etc/nginx/sites-available/arvion
ln -sfn /etc/nginx/sites-available/arvion /etc/nginx/sites-enabled/arvion
rm -f /etc/nginx/sites-enabled/default

sudo -u "$APP_USER" env APP_DIR="$APP_DIR" ENV_FILE="$ENV_FILE" "$APP_DIR/ops/release.sh"
systemctl daemon-reload
systemctl enable --now arvion.service arvion-traffic-cleanup.timer nginx
nginx -t
set -a
source "$ENV_FILE"
set +a
HEALTH_HOST="${DJANGO_ALLOWED_HOSTS%%,*}"
curl --fail --silent --show-error --retry 10 --retry-delay 2 \
  --header "Host: $HEALTH_HOST" --header "X-Forwarded-Proto: https" \
  http://127.0.0.1:8000/health/ >/dev/null
echo "Arvion is running. Configure Arvan DNS/CDN and TLS, then verify the public /health/ endpoint."
