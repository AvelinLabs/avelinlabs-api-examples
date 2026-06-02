#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-https://api.avelinlabs.com}"
: "${AVELIN_API_KEY:?Set AVELIN_API_KEY before running this example.}"

curl -sS \
  "${BASE_URL}/api/v1/market/top?type=technology&scope=active&country=US&limit=5" \
  -H "Authorization: Bearer ${AVELIN_API_KEY}"
