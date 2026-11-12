#!/usr/bin/env bash
set -euo pipefail
umask 077
if [[ ${1:-} != --apply ]]; then
  echo 'Restore only to an empty omnisight_restore_* database, offline. Pass --apply to execute.' >&2
  exit 2
fi
: "${PGHOST:?Set PGHOST}" "${PGDATABASE:?Set PGDATABASE}" "${PGUSER:?Set PGUSER}"
: "${BACKUP_FILE:?Set encrypted backup}" "${AGE_IDENTITY_FILE:?Set protected private identity}"
: "${DELETION_LEDGER_PATH:?Set independent latest ledger}" "${DELETION_LEDGER_KEY:?Set original ledger signing key}"
: "${DELETION_LEDGER_SHA256:?Set independently retained current ledger checkpoint}"
if [[ ! $PGDATABASE =~ ^omnisight_restore_[a-zA-Z0-9_]+$ ]]; then
  echo 'RESTORE_BLOCKED: database must use the isolated omnisight_restore_ prefix.' >&2
  exit 2
fi
cd -- "$(dirname -- "$0")/../.."
# Derive Django's connection from the SAME libpq target. No password in argv.
# libpq uses PGPASSFILE/PGPASSWORD and the existing PGSSL* settings.
export DATABASE_URL
DATABASE_URL=$(python3 - <<'PY'
import os
from urllib.parse import quote
print('postgresql://' + quote(os.environ['PGUSER'],safe='') + '@' + os.environ['PGHOST'] + ':' + os.environ.get('PGPORT','5432') + '/' + quote(os.environ['PGDATABASE'],safe=''))
PY
)
python3 apps/api/manage.py reapply_deletions --ledger "$DELETION_LEDGER_PATH" --expected-sha256 "$DELETION_LEDGER_SHA256" --validate-only > /dev/null
tables=$(psql --no-psqlrc --tuples-only --no-align --command "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")
if [[ $tables != 0 ]]; then
  echo 'RESTORE_BLOCKED: target database is not empty.' >&2
  exit 2
fi
if ! age --decrypt --identity "$AGE_IDENTITY_FILE" "$BACKUP_FILE" | pg_restore --single-transaction --exit-on-error --no-owner --no-acl --dbname "$PGDATABASE"; then
  echo 'RESTORE_FAILED: leave target isolated; do not reopen traffic.' >&2
  exit 1
fi
python3 apps/api/manage.py migrate --noinput
python3 apps/api/manage.py reapply_deletions --ledger "$DELETION_LEDGER_PATH" --expected-sha256 "$DELETION_LEDGER_SHA256" --apply
python3 apps/api/manage.py shell <<'PY'
from identity.privacy import purge_expired
from rest_framework.authtoken.models import Token
from django.contrib.sessions.models import Session
Token.objects.all().delete()
Session.objects.all().delete()
while True:
    result = purge_expired(batch_size=1000)
    if not result['scansDeleted'] and not result['bucketsDeleted']:
        break
print('RESTORE_SANITIZED: sessions revoked and retention applied.')
PY
echo 'RESTORE_READY_FOR_REVIEW: keep offline until data, password recovery and smoke checks are approved.'
