#!/bin/sh
set -eu
if [ "${DELETION_LEDGER_PATH:-}" != /data/privacy-ledger/deletions.jsonl ]; then
  echo 'Configure DELETION_LEDGER_PATH=/data/privacy-ledger/deletions.jsonl' >&2
  exit 1
fi
# Railway volumes start root-owned. Initialise only the journal directory;
# migrations and the application run as app, after the real volume is mounted.
test "${RAILWAY_VOLUME_MOUNT_PATH:-}" = /data || {
  echo 'Mount a persistent Railway volume at /data before starting the API' >&2
  exit 1
}
mkdir -p /data/privacy-ledger
chown app:app /data/privacy-ledger
chmod 700 /data/privacy-ledger
gosu app python manage.py migrate --noinput
exec gosu app "$@"
