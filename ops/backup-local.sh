#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/srv/arvion}"
BACKUP_DIR="${BACKUP_DIR:-$APP_DIR/backups/daily}"
DATABASE="${BACKUP_DATABASE:-arvion}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
STAMP="$(date -u +%Y%m%d-%H%M%S)"

install -d -m 0750 -o arvion -g arvion "$BACKUP_DIR"
DB_FILE="$BACKUP_DIR/postgres-$STAMP.dump"
MEDIA_FILE="$BACKUP_DIR/media-$STAMP.tar.gz"

sudo -u postgres pg_dump --format=custom --no-owner --no-privileges "$DATABASE" > "$DB_FILE"
test -s "$DB_FILE"
chown arvion:arvion "$DB_FILE"

if [[ -d "$APP_DIR/media" ]]; then
  tar -C "$APP_DIR" -czf "$MEDIA_FILE" media
else
  tar -czf "$MEDIA_FILE" --files-from /dev/null
fi
test -s "$MEDIA_FILE"
chown arvion:arvion "$MEDIA_FILE"

# Retention is intentionally limited to dated daily archives in this exact directory.
find "$BACKUP_DIR" -maxdepth 1 -type f \( -name 'postgres-*.dump' -o -name 'media-*.tar.gz' \) -mtime "+$RETENTION_DAYS" -delete
echo "Daily backup completed: $DB_FILE and $MEDIA_FILE"
