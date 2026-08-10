# Response Examples

These files show response shapes; they are not substitutes for the API contract. Provenance is recorded here so repository metadata never appears inside an API payload.

| Files | Classification | Provenance |
| --- | --- | --- |
| `health-live.example.json`, `health-ready.example.json` | Sanitized live output | Recorded from PROD on 2026-08-10. The payloads contain no identifiers or secrets. |
| `error-invalid-api-key.example.json` | Sanitized fixture derived from live behavior | Field names and stable values were checked against a controlled PROD `401`; `request_id` is a placeholder, not a captured production value. |
| `occupation-candidates.example.json` | Illustrative output fixture | Synthetic, OpenAPI-valid output for the synthetic request in `payloads/occupation-candidates.json`. It is not a live snapshot and intentionally shows five candidate objects for `limit: 5`. |
| All other `.example.json` files in this directory | Illustrative output fixtures | Synthetic, realistic examples validated against the matching response schema where OpenAPI defines one. Counts, scores, identifiers, and text are not claimed as production observations. |

Executable request fixtures live separately in `payloads/`, `input-quality/`, and `customer-grounding/requests/`. Placeholder values such as `<runtime-model-version>` are intentional. Volatile identifiers and counts may differ between calls, and clients should ignore unknown additive fields.

The authoritative machine-readable contract is https://api.avelinlabs.com/openapi.json.
