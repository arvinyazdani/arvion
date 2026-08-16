#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/srv/arvion}"
ENV_FILE="${ENV_FILE:-$APP_DIR/.env.production}"
BACKUP_DIR="${BACKUP_DIR:-$APP_DIR/backups}"
BACKUP_DATABASE="${BACKUP_DATABASE:-arvion}"
RELEASE_STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_FILE="$BACKUP_DIR/pre-release-$RELEASE_STAMP.dump"

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
systemctl daemon-reload
systemctl enable --now arvion-notifications.timer arvion-healthcheck.timer arvion-backup.timer
systemctl restart arvion
systemctl is-active --quiet arvion
