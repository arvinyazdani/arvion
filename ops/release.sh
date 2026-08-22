#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/srv/arvion}"
APP_USER="${APP_USER:-arvion}"
ENV_FILE="${ENV_FILE:-$APP_DIR/.env.production}"
BACKUP_DIR="${BACKUP_DIR:-$APP_DIR/backups}"
BACKUP_DATABASE="${BACKUP_DATABASE:-arvion}"
RELEASE_STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_FILE="$BACKUP_DIR/pre-release-$RELEASE_STAMP.dump"
RELEASE_LOG="$BACKUP_DIR/release-history.log"
NGINX_TARGET="/etc/nginx/sites-available/arvion"
NGINX_BACKUP="$BACKUP_DIR/nginx-pre-release-$RELEASE_STAMP.conf"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this release script with sudo so it can create the PostgreSQL snapshot." >&2
  exit 1
fi

install -d -m 0750 -o arvion -g arvion "$BACKUP_DIR"
sudo -u postgres pg_dump --format=custom --no-owner --no-privileges "$BACKUP_DATABASE" > "$BACKUP_FILE"
chown arvion:arvion "$BACKUP_FILE"
test -s "$BACKUP_FILE"
echo "Pre-release database snapshot: $BACKUP_FILE"

cd "$APP_DIR"
RELEASE_COMMIT="$(git -c safe.directory="$APP_DIR" -C "$APP_DIR" rev-parse --short HEAD)"

# Give every monitoring event a release identifier without putting a DSN or
# other secret in Git.  The environment file is read by systemd at restart.
if grep -q '^SENTRY_RELEASE=' "$ENV_FILE"; then
  sed -i "s/^SENTRY_RELEASE=.*/SENTRY_RELEASE=rvion-$RELEASE_COMMIT/" "$ENV_FILE"
else
  printf '\nSENTRY_RELEASE=rvion-%s\n' "$RELEASE_COMMIT" >> "$ENV_FILE"
fi
chown "$APP_USER:$APP_USER" "$ENV_FILE"
chmod 0600 "$ENV_FILE"

# Install the exact dependencies of the checked-out release before importing
# Django settings.  Running pip as the application user keeps the virtualenv
# ownership stable across releases.
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/python" -m pip install \
  --disable-pip-version-check --requirement "$APP_DIR/requirements.txt"
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/python" -m pip check

run_manage() {
  sudo -u "$APP_USER" bash -c "set -a; source '$ENV_FILE'; set +a; DJANGO_SETTINGS_MODULE=arvion.settings.production '$APP_DIR/.venv/bin/python' '$APP_DIR/manage.py' $*"
}

run_manage check --deploy
run_manage migrate --noinput
run_manage setup_staff_roles
run_manage seed_assessment_banks
run_manage collectstatic --noinput

# Keep the active Nginx configuration in sync with the release, but never
# leave an invalid candidate in place.  The previous file is retained beside
# the database snapshot for an immediate operational rollback.
if [[ -f "$NGINX_TARGET" ]]; then
  cp --preserve=mode,ownership,timestamps "$NGINX_TARGET" "$NGINX_BACKUP"
fi
install -m 0644 "$APP_DIR/ops/nginx.conf" "$NGINX_TARGET"
if ! nginx -t; then
  if [[ -f "$NGINX_BACKUP" ]]; then
    install -m 0644 "$NGINX_BACKUP" "$NGINX_TARGET"
  else
    rm -f "$NGINX_TARGET"
  fi
  nginx -t || true
  echo "Nginx candidate was invalid; the previous configuration was restored." >&2
  exit 1
fi

install -m 0644 "$APP_DIR/ops/arvion-notifications.service" /etc/systemd/system/arvion-notifications.service
install -m 0644 "$APP_DIR/ops/arvion-notifications.timer" /etc/systemd/system/arvion-notifications.timer
install -m 0644 "$APP_DIR/ops/arvion-healthcheck.service" /etc/systemd/system/arvion-healthcheck.service
install -m 0644 "$APP_DIR/ops/arvion-healthcheck.timer" /etc/systemd/system/arvion-healthcheck.timer
install -m 0644 "$APP_DIR/ops/arvion-system-log-cleanup.service" /etc/systemd/system/arvion-system-log-cleanup.service
install -m 0644 "$APP_DIR/ops/arvion-system-log-cleanup.timer" /etc/systemd/system/arvion-system-log-cleanup.timer
install -m 0750 "$APP_DIR/ops/backup-local.sh" /usr/local/sbin/arvion-backup-local
install -m 0644 "$APP_DIR/ops/arvion-backup.service" /etc/systemd/system/arvion-backup.service
install -m 0644 "$APP_DIR/ops/arvion-backup.timer" /etc/systemd/system/arvion-backup.timer
install -m 0750 "$APP_DIR/ops/restore-check.sh" /usr/local/sbin/arvion-restore-check
install -m 0644 "$APP_DIR/ops/arvion-restore-check.service" /etc/systemd/system/arvion-restore-check.service
install -m 0644 "$APP_DIR/ops/arvion-restore-check.timer" /etc/systemd/system/arvion-restore-check.timer
systemctl daemon-reload
systemctl enable --now arvion-notifications.timer arvion-healthcheck.timer arvion-system-log-cleanup.timer arvion-backup.timer arvion-restore-check.timer
systemctl restart arvion
systemctl is-active --quiet arvion
if ! systemctl reload nginx; then
  if [[ -f "$NGINX_BACKUP" ]]; then
    install -m 0644 "$NGINX_BACKUP" "$NGINX_TARGET"
    nginx -t
    systemctl reload nginx
  fi
  echo "Nginx reload failed; the previous configuration was restored." >&2
  exit 1
fi

# The application is deliberately probed locally: DNS/CDN failures must not make
# a healthy deployment look unsuccessful, while the Host header still exercises
# Django's production host and HTTPS-aware settings.
set -a
source "$ENV_FILE"
set +a
HEALTH_HOST="${DJANGO_ALLOWED_HOSTS%%,*}"
HEALTH_URL="http://127.0.0.1:8000/health/"
for attempt in {1..15}; do
  if curl --fail --silent --connect-timeout 3 \
    --header "Host: $HEALTH_HOST" \
    --header "X-Forwarded-Proto: https" \
    "$HEALTH_URL" >/dev/null; then
    break
  fi

  if [[ "$attempt" -eq 15 ]]; then
    echo "Application health check failed after restart." >&2
    exit 1
  fi
  sleep 1
done

printf '%s commit=%s snapshot=%s health=ok\n' \
  "$(date --iso-8601=seconds)" "$RELEASE_COMMIT" "$BACKUP_FILE" >> "$RELEASE_LOG"
chown arvion:arvion "$RELEASE_LOG"
chmod 0640 "$RELEASE_LOG"
echo "Release completed: commit=$RELEASE_COMMIT health=ok"
