#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-https://api.avelinlabs.com}"
: "${AVELIN_API_KEY:?Set AVELIN_API_KEY before running this example.}"

SOURCE_ID="${SOURCE_ID:-synthetic-file-validation-$(date +%s)}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

api() {
  curl -sS "$@" -H "Authorization: Bearer ${AVELIN_API_KEY}" -H "Accept: application/json"
}

json_api() {
  api "$@" -H "Content-Type: application/json"
}

python - "$EXAMPLE_ROOT/requests/register-source.json" "$SOURCE_ID" <<'PY' > "${TMP_DIR}/register.json"
import json
import sys
path, source_id = sys.argv[1], sys.argv[2]
payload = json.load(open(path, encoding="utf-8"))
payload["source_id"] = source_id
print(json.dumps(payload))
PY

json_api -X POST "${BASE_URL}/api/v1/grounding/sources" --data-binary "@${TMP_DIR}/register.json" >/dev/null

printf 'not a pdf\n' > "${TMP_DIR}/corrupt.pdf"
printf 'unsupported\n' > "${TMP_DIR}/unsupported.rtf"
python - "${TMP_DIR}/oversized.txt" <<'PY'
import sys
open(sys.argv[1], "wb").write(b"x" * (5 * 1024 * 1024 + 1))
PY

echo "customer_id rejection"
json_api -X POST "${BASE_URL}/api/v1/grounding/sources/${SOURCE_ID}/ingest-text" \
  --data-binary "@${EXAMPLE_ROOT}/requests/customer-id-rejection.json" || true
echo

echo "unsupported file type"
api -X POST "${BASE_URL}/api/v1/grounding/sources/${SOURCE_ID}/ingest-file" \
  -F "file=@${TMP_DIR}/unsupported.rtf;type=application/rtf" || true
echo

echo "extension/MIME mismatch"
api -X POST "${BASE_URL}/api/v1/grounding/sources/${SOURCE_ID}/ingest-file" \
  -F "file=@${EXAMPLE_ROOT}/sample-files/synthetic-role-criteria.pdf;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document" || true
echo

echo "corrupt PDF"
api -X POST "${BASE_URL}/api/v1/grounding/sources/${SOURCE_ID}/ingest-file" \
  -F "file=@${TMP_DIR}/corrupt.pdf;type=application/pdf" || true
echo

echo "oversized file"
api -X POST "${BASE_URL}/api/v1/grounding/sources/${SOURCE_ID}/ingest-file" \
  -F "file=@${TMP_DIR}/oversized.txt;type=text/plain" || true
echo

json_api -X DELETE "${BASE_URL}/api/v1/grounding/sources/${SOURCE_ID}" --data-binary "@${EXAMPLE_ROOT}/requests/delete-source.json" >/dev/null || true
