#!/usr/bin/env bash
set -Eeuo pipefail

BACKUP_DIR="${BACKUP_DIR:-/srv/arvion/backups/daily}"
SOURCE_DB="${BACKUP_DATABASE:-arvion}"
STAMP="$(date -u +%Y%m%d%H%M%S)"
TEST_DB="arvion_restore_check_$STAMP"
LATEST="$(find "$BACKUP_DIR" -maxdepth 1 -type f -name 'postgres-*.dump' -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-)"
RESTORE_FILE="/var/tmp/$TEST_DB.dump"

test -n "$LATEST" && test -s "$LATEST"
cleanup(){ rm -f "$RESTORE_FILE"; sudo -u postgres dropdb --if-exists "$TEST_DB"; }
trap cleanup EXIT

install -m 0640 -o postgres -g postgres "$LATEST" "$RESTORE_FILE"
sudo -u postgres createdb -T template0 "$TEST_DB"
sudo -u postgres pg_restore --no-owner --no-privileges --dbname="$TEST_DB" "$RESTORE_FILE"
sudo -u postgres psql --dbname="$TEST_DB" --tuples-only --no-align --command='SELECT 1' | grep -qx '1'
echo "Restore drill succeeded from $(basename "$LATEST") into temporary database $TEST_DB"
