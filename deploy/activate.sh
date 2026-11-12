#!/usr/bin/env bash
# Executed on the provisioned host after a successful CI run and SSH transfer.
set -euo pipefail
release_sha=${1:?Pass commit SHA}
transfer_id=${2:?Pass transfer ID}
[[ "$release_sha" =~ ^[0-9a-f]{40}$ ]] || exit 2
[[ "$transfer_id" =~ ^[0-9]+-[0-9]+$ ]] || exit 2
root=/opt/omnisight
env_file=$root/shared/production.env
incoming=$root/incoming/$transfer_id
release=$root/releases/$release_sha
test -f "$env_file"
test -d "$incoming/images"
mkdir -p "$root/releases"
exec 9>"$root/deploy.lock"
flock -n 9 || { echo 'Another deployment is running' >&2; exit 1; }
# Each SHA gets its own immutable release directory. Persistent volumes retain
# the established Compose project name, independently of checkout location.
test ! -e "$release" || { echo 'Release already exists; inspect it before retrying' >&2; exit 1; }
mkdir "$release"
cp -a "$incoming/deploy" "$release/deploy"
export RELEASE_SHA=$release_sha
compose=(docker compose --project-name omnisight --env-file "$env_file" -f "$release/deploy/compose.yml" -f "$release/deploy/compose.release.yml")
"${compose[@]}" config --quiet
for service in api browser web backup; do
  gzip -dc "$incoming/images/$service.tar.gz" | docker load
  docker image inspect "omnisight/$service:$release_sha" >/dev/null
done
# Never down -v. Backups and schema rollback require a separate recovery runbook.
# A pre-upgrade encrypted backup is required once a database already exists.
if "${compose[@]}" ps --status running --services | grep -qx db; then
  "${compose[@]}" run --rm --no-build backup
fi
"${compose[@]}" up -d db
# run --rm guarantees every release executes migrations, even if an old migrate
# container previously exited successfully. Do not migrate backwards on failure.
"${compose[@]}" stop api worker retention
"${compose[@]}" run --rm --no-build migrate
"${compose[@]}" up -d --no-build --force-recreate --wait --wait-timeout 180
app_domain=$("${compose[@]}" exec -T api python -c 'from django.conf import settings; print(settings.ALLOWED_HOSTS[0])')
healthy=false
for attempt in {1..12}; do
  if APP_DOMAIN=$app_domain sh "$release/deploy/smoke.sh"; then
    healthy=true
    break
  fi
  sleep 5
done
"$healthy" || { echo 'HTTPS smoke failed; inspect services before retry or rollback' >&2; exit 1; }
# Only mark a release current after health/smoke pass. A failed deploy can have
# modified schema/services: do not present the previous symlink as a rollback.
ln -sfn "$release" "$root/current"
printf '%s\n' "$release_sha" > "$root/deployed-sha"
# Images are retained for manual code rollback; transferred archives are disposable.
rm -f "$incoming/images/"*.tar.gz "$incoming/release.tar.gz"
echo "Healthy release: $release_sha"
