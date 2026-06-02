#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-https://api.avelinlabs.com}"
: "${AVELIN_API_KEY:?Set AVELIN_API_KEY before running this example.}"

curl -sS \
  -X POST "${BASE_URL}/api/v1/job/classify" \
  -H "Authorization: Bearer ${AVELIN_API_KEY}" \
  -H "Content-Type: application/json" \
  --data-binary "@api-examples/payloads/job-classify.json"
