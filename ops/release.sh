#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/srv/arvion}"
ENV_FILE="${ENV_FILE:-$APP_DIR/.env.production}"
BACKUP_DIR="${BACKUP_DIR:-$APP_DIR/backups}"
BACKUP_DATABASE="${BACKUP_DATABASE:-arvion}"
RELEASE_STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_FILE="$BACKUP_DIR/pre-release-$RELEASE_STAMP.dump"
RELEASE_LOG="$BACKUP_DIR/release-history.log"

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
RELEASE_COMMIT="$(git rev-parse --short HEAD)"
run_manage() {
  sudo -u arvion bash -c "set -a; source '$ENV_FILE'; set +a; DJANGO_SETTINGS_MODULE=arvion.settings.production '$APP_DIR/.venv/bin/python' '$APP_DIR/manage.py' $*"
}

run_manage check --deploy
run_manage migrate --noinput
run_manage setup_staff_roles
run_manage seed_assessment_banks
run_manage collectstatic --noinput
install -m 0644 "$APP_DIR/ops/arvion-notifications.service" /etc/systemd/system/arvion-notifications.service
install -m 0644 "$APP_DIR/ops/arvion-notifications.timer" /etc/systemd/system/arvion-notifications.timer
install -m 0644 "$APP_DIR/ops/arvion-healthcheck.service" /etc/systemd/system/arvion-healthcheck.service
install -m 0644 "$APP_DIR/ops/arvion-healthcheck.timer" /etc/systemd/system/arvion-healthcheck.timer
install -m 0750 "$APP_DIR/ops/backup-local.sh" /usr/local/sbin/arvion-backup-local
install -m 0644 "$APP_DIR/ops/arvion-backup.service" /etc/systemd/system/arvion-backup.service
install -m 0644 "$APP_DIR/ops/arvion-backup.timer" /etc/systemd/system/arvion-backup.timer
install -m 0750 "$APP_DIR/ops/restore-check.sh" /usr/local/sbin/arvion-restore-check
install -m 0644 "$APP_DIR/ops/arvion-restore-check.service" /etc/systemd/system/arvion-restore-check.service
install -m 0644 "$APP_DIR/ops/arvion-restore-check.timer" /etc/systemd/system/arvion-restore-check.timer
systemctl daemon-reload
systemctl enable --now arvion-notifications.timer arvion-healthcheck.timer arvion-backup.timer arvion-restore-check.timer
systemctl restart arvion
systemctl is-active --quiet arvion

# The application is deliberately probed locally: DNS/CDN failures must not make
# a healthy deployment look unsuccessful, while the Host header still exercises
# Django's production host and HTTPS-aware settings.
set -a
source "$ENV_FILE"
set +a
HEALTH_HOST="${DJANGO_ALLOWED_HOSTS%%,*}"
curl --fail --silent --show-error --connect-timeout 10 \
  --header "Host: $HEALTH_HOST" \
  --header "X-Forwarded-Proto: https" \
  http://127.0.0.1:8000/health/ >/dev/null

printf '%s commit=%s snapshot=%s health=ok\n' \
  "$(date --iso-8601=seconds)" "$RELEASE_COMMIT" "$BACKUP_FILE" >> "$RELEASE_LOG"
chown arvion:arvion "$RELEASE_LOG"
chmod 0640 "$RELEASE_LOG"
echo "Release completed: commit=$RELEASE_COMMIT health=ok"
