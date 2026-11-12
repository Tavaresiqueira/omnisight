#!/usr/bin/env bash
set -euo pipefail
umask 077
: "${PGHOST:?Set PGHOST}" "${PGDATABASE:?Set PGDATABASE}" "${PGUSER:?Set PGUSER}"
: "${AGE_RECIPIENT:?Set age public recipient}" "${BACKUP_DIR:?Set protected backup directory}"
retention=${BACKUP_RETENTION_DAYS:-7}
if [[ ! $retention =~ ^[1-9][0-9]{0,2}$ ]] || (( retention > 365 )); then
  echo 'BACKUP_FAILED: retention must be 1-365 days.' >&2
  exit 2
fi
mkdir -p "$BACKUP_DIR"
tmp=$(mktemp "$BACKUP_DIR/backup-XXXXXXXX")
trap 'rm -f -- "$tmp"' EXIT
if ! pg_dump --format=custom --no-owner --no-acl | age --encrypt --recipient "$AGE_RECIPIENT" > "$tmp"; then
  echo 'BACKUP_FAILED: dump/encryption failed; notify operator.' >&2
  exit 1
fi
target="$tmp.age"
mv -- "$tmp" "$target"
sha256sum -- "$target" > "$target.sha256"
# Only prune this application's encrypted files after a successful new backup.
find "$BACKUP_DIR" -maxdepth 1 -type f \( -name 'backup-*.age' -o -name 'backup-*.age.sha256' \) -mmin "+$((retention * 1440))" -delete
echo "BACKUP_OK: $target"
