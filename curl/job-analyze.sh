#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-https://api.avelinlabs.com}"
: "${AVELIN_API_KEY:?Set AVELIN_API_KEY before running this example.}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

curl -sS \
  -X POST "${BASE_URL}/api/v1/job/analyze" \
  -H "Authorization: Bearer ${AVELIN_API_KEY}" \
  -H "Content-Type: application/json" \
  --data-binary "@${REPO_ROOT}/payloads/job-analyze.json"
