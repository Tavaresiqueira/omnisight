#!/bin/sh
set -eu
: "${APP_DOMAIN:?Set APP_DOMAIN}"
curl --fail --silent --show-error --max-time 15 "https://${APP_DOMAIN}/api/health/"
curl --fail --silent --show-error --max-time 15 -o /dev/null "https://${APP_DOMAIN}/"
