#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-https://api.avelinlabs.com}"
: "${AVELIN_API_KEY:?Set AVELIN_API_KEY to a Runtime API Key.}"

curl --fail-with-body --silent --show-error \
  "${BASE_URL%/}/api/v1/workforce/capabilities?country_code=US" \
  -H "Authorization: Bearer ${AVELIN_API_KEY}" \
  -H "Accept: application/json"

printf '\n'
