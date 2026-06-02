#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-https://api.avelinlabs.com}"
ONET_CODE="${ONET_CODE:-15-1252.00}"
: "${AVELIN_API_KEY:?Set AVELIN_API_KEY before running this example.}"

curl -sS \
  "${BASE_URL}/api/v1/occupation/profile/${ONET_CODE}" \
  -H "Authorization: Bearer ${AVELIN_API_KEY}"
