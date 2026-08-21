#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-https://api.avelinlabs.com}"
: "${AVELIN_API_KEY:?Set AVELIN_API_KEY to a Runtime API Key.}"
: "${EVIDENCE_PACK_ID:?Set EVIDENCE_PACK_ID to the identifier returned by creation.}"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_dir="${OUTPUT_DIR:-${repo_root}/workforce-evidence-pack/output}"
mkdir -p "${output_dir}"

curl --fail-with-body --silent --show-error \
  "${BASE_URL%/}/api/v1/workforce/evidence-packs/${EVIDENCE_PACK_ID}/report?format=html" \
  -H "Authorization: Bearer ${AVELIN_API_KEY}" \
  -H "Accept: text/html" \
  --output "${output_dir}/${EVIDENCE_PACK_ID}.html"

printf 'Saved %s\n' "${output_dir}/${EVIDENCE_PACK_ID}.html"
