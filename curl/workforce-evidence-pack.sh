#!/usr/bin/env bash
set -euo pipefail

: "${BASE_URL:?Set BASE_URL to an environment where the controlled-beta Workforce API is enabled.}"
: "${AVELIN_API_KEY:?Set AVELIN_API_KEY to a Runtime API Key.}"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

curl --fail-with-body --silent --show-error \
  -X POST "${BASE_URL%/}/api/v1/workforce/evidence-packs" \
  -H "Authorization: Bearer ${AVELIN_API_KEY}" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  --data "@${repo_root}/workforce-evidence-pack/request.json"

printf '\n'
