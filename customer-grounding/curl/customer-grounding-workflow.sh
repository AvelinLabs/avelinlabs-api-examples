#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-https://api.avelinlabs.com}"
: "${AVELIN_API_KEY:?Set AVELIN_API_KEY before running this example.}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SOURCE_ID="${SOURCE_ID:-synthetic-role-criteria-$(date +%s)}"

api() {
  curl -sS "$@" -H "Authorization: Bearer ${AVELIN_API_KEY}" -H "Accept: application/json"
}

json_api() {
  api "$@" -H "Content-Type: application/json"
}

echo "Capabilities"
api "${BASE_URL}/api/v1/grounding/capabilities"
echo

echo "Register source: ${SOURCE_ID}"
python - "$EXAMPLE_ROOT/requests/register-source.json" "$SOURCE_ID" <<'PY' > "${EXAMPLE_ROOT}/.register-source.generated.json"
import json
import sys
path, source_id = sys.argv[1], sys.argv[2]
payload = json.load(open(path, encoding="utf-8"))
payload["source_id"] = source_id
print(json.dumps(payload))
PY
json_api -X POST "${BASE_URL}/api/v1/grounding/sources" --data-binary "@${EXAMPLE_ROOT}/.register-source.generated.json"
echo

echo "List sources"
api "${BASE_URL}/api/v1/grounding/sources"
echo

echo "Get source"
api "${BASE_URL}/api/v1/grounding/sources/${SOURCE_ID}"
echo

echo "Ingest text"
TEXT_RESPONSE="$(
  json_api -X POST "${BASE_URL}/api/v1/grounding/sources/${SOURCE_ID}/ingest-text" \
    --data-binary "@${EXAMPLE_ROOT}/requests/ingest-text.json"
)"
printf '%s\n' "$TEXT_RESPONSE"
INGESTION_RUN_ID="$(printf '%s' "$TEXT_RESPONSE" | python -c "import json,sys; print(json.load(sys.stdin)['ingestion_run']['ingestion_run_id'])")"

echo "Ingest supported files"
api -X POST "${BASE_URL}/api/v1/grounding/sources/${SOURCE_ID}/ingest-file" \
  -F "version_label=synthetic-txt-v1" \
  -F "file=@${EXAMPLE_ROOT}/sample-files/synthetic-role-criteria.txt;type=text/plain"
echo
api -X POST "${BASE_URL}/api/v1/grounding/sources/${SOURCE_ID}/ingest-file" \
  -F "version_label=synthetic-md-v1" \
  -F "file=@${EXAMPLE_ROOT}/sample-files/synthetic-role-criteria.md;type=text/markdown"
echo
api -X POST "${BASE_URL}/api/v1/grounding/sources/${SOURCE_ID}/ingest-file" \
  -F "version_label=synthetic-pdf-v1" \
  -F "file=@${EXAMPLE_ROOT}/sample-files/synthetic-role-criteria.pdf;type=application/pdf"
echo
api -X POST "${BASE_URL}/api/v1/grounding/sources/${SOURCE_ID}/ingest-file" \
  -F "version_label=synthetic-docx-v1" \
  -F "file=@${EXAMPLE_ROOT}/sample-files/synthetic-role-criteria.docx;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document"
echo

echo "List versions"
api "${BASE_URL}/api/v1/grounding/sources/${SOURCE_ID}/versions"
echo

echo "List artifacts"
api "${BASE_URL}/api/v1/grounding/sources/${SOURCE_ID}/artifacts"
echo

echo "Get ingestion run"
api "${BASE_URL}/api/v1/grounding/ingestion-runs/${INGESTION_RUN_ID}"
echo

echo "Generate report"
REPORT_RESPONSE="$(
  json_api -X POST "${BASE_URL}/api/v1/grounding/role-intelligence/reports" \
    --data-binary "@${EXAMPLE_ROOT}/requests/role-intelligence-report.json"
)"
printf '%s\n' "$REPORT_RESPONSE"
TRACE_ID="$(printf '%s' "$REPORT_RESPONSE" | python -c "import json,sys; print(json.load(sys.stdin)['trace_id'])")"

echo "Get trace"
api "${BASE_URL}/api/v1/grounding/traces/${TRACE_ID}"
echo

echo "Disable source"
json_api -X POST "${BASE_URL}/api/v1/grounding/sources/${SOURCE_ID}/disable" --data-binary "{}"
echo

echo "Enable source"
json_api -X POST "${BASE_URL}/api/v1/grounding/sources/${SOURCE_ID}/enable" --data-binary "{}"
echo

echo "Delete source"
json_api -X DELETE "${BASE_URL}/api/v1/grounding/sources/${SOURCE_ID}" --data-binary "@${EXAMPLE_ROOT}/requests/delete-source.json"
echo

rm -f "${EXAMPLE_ROOT}/.register-source.generated.json"
