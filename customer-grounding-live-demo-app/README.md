# Customer Grounding Live Demo App

Status: local evaluator/developer demo for AvelinLabs Customer Grounding controlled beta.

This folder contains a real local demo app. It serves a static browser UI and a local-only Python proxy that calls the existing AvelinLabs Customer Grounding Runtime API endpoints. It replaces the previous static mini-dashboard example.

The app is not a hosted production UI, not a deployment, and not a final hiring decision tool. It is a local adoption demo for API-first and MCP-first Customer Grounding workflows.

## What It Does

- Connects to an AvelinLabs backend with a Runtime API key.
- Calls `GET /api/v1/grounding/capabilities` to verify access.
- Registers a source with `POST /api/v1/grounding/sources`.
- Ingests synthetic Markdown/text through `POST /api/v1/grounding/sources/{source_id}/ingest-text`.
- Forwards approved local files through `POST /api/v1/grounding/sources/{source_id}/ingest-file`.
- Generates grounded Role Intelligence with `POST /api/v1/grounding/role-intelligence/reports`.
- Fetches trace details with `GET /api/v1/grounding/traces/{trace_id}`.
- Fetches usage with `GET /api/v1/grounding/usage` when available.
- Cleans up demo sources with `DELETE /api/v1/grounding/sources/{source_id}`.
- Provides copyable cURL and MCP examples for adoption.

## Files

- `server.py` - local static server and proxy. Uses Python standard library only.
- `create_demo_runtime_key.py` - internal/local DEV-only helper for AvelinLabs development and testing when no onboarded customer key is available.
- `index.html` - guided demo UI.
- `styles.css` - local app styling.
- `app.js` - browser workflow logic.
- `assets/avelinlabs-logo.png` - local AvelinLabs logo asset.
- `samples/` - synthetic customer-context Markdown samples.

## Prerequisites

- AvelinLabs API Base URL.
- One onboarding Runtime API key provided by AvelinLabs whose contract allows `/api/v1/grounding`.
- Python 3.10+.

## Recommended Customer / Evaluator Flow

For customer or evaluator use, the recommended manual flow is:

1. Start the local demo app.
2. Open `http://127.0.0.1:<port>/`.
3. Enter the API Base URL and the Runtime API key provided by AvelinLabs during onboarding into the UI.
4. Test capabilities.
5. Use the same key for Customer Grounding API calls, report generation, trace lookup, usage, and cleanup.

Customers do not need two keys. The onboarding Runtime API key is sufficient when its contract includes `/api/v1/grounding`. If the key lacks `/api/v1/grounding`, AvelinLabs onboarding/provisioning must update or replace that key. The customer should not create a separate DEV key.

The demo app keeps the configured key in local server process memory only. It does not write the key to repo files, `.env` files, browser `localStorage`, or browser `sessionStorage`.

## Internal DEV-Only Temporary Key Helper

`create_demo_runtime_key.py` is internal/local DEV-only AvelinLabs tooling. It is for local development and testing when no onboarded customer Runtime API key is available. It is not part of customer onboarding, must not be used for production, and must not be used to grant customer-hosted access.

Use this helper only with a local/development backend and the same SQL-backed local platform DB configuration and `AVELIN_PLATFORM_API_KEY_SECRET` used by that backend. The helper can load a local untracked backend `.env` file without printing values. It refuses strict production mode, refuses non-localhost API base URLs, refuses process-local in-memory platform mode, refuses env files under `C:\_prod`, creates or reuses a synthetic `.local` demo user, creates a short-lived contract scoped only to `/api/v1/grounding`, stores the key through the existing Runtime API key model, and prints the raw key once.

PowerShell:

```powershell
cd C:\_dev\avelinlabs-api-examples\customer-grounding-live-demo-app
$envFile = "C:\_dev\avelin\backend\.env"  # local untracked env file used by the running DEV backend

C:\programdata\anaconda3\envs\skillvista\python.exe create_demo_runtime_key.py --dev-mode local --env-file $envFile create --ttl-hours 4

$env:AVELIN_API_BASE = "http://127.0.0.1:8010"
$env:AVELIN_RUNTIME_API_KEY = "<printed-key>"

C:\programdata\anaconda3\envs\skillvista\python.exe smoke_live_demo.py

C:\programdata\anaconda3\envs\skillvista\python.exe server.py --host 127.0.0.1 --port 8788
```

After the smoke/demo, revoke the temporary key:

```powershell
C:\programdata\anaconda3\envs\skillvista\python.exe create_demo_runtime_key.py --dev-mode local --env-file $envFile revoke --key-id <key-id>
```

If your shell already has the same platform DB settings and `AVELIN_PLATFORM_API_KEY_SECRET` as the running backend, omit `--env-file`. Do not paste the printed key or env-file secret values into docs, screenshots, tickets, chat, or committed files.

## Run Locally

PowerShell:

```powershell
cd customer-grounding-live-demo-app
C:\programdata\anaconda3\envs\skillvista\python.exe server.py --host 127.0.0.1 --port 8765
```

Open:

```text
http://127.0.0.1:8765/
```

Then enter the API Base URL and onboarding Runtime API key in the UI.

Environment variables are optional for normal customer/evaluator UI use. They are useful for `smoke_live_demo.py`, headless/internal developer testing, and repeatable local QA:

```powershell
$env:AVELIN_API_BASE = "http://127.0.0.1:8010"
$env:AVELIN_RUNTIME_API_KEY = "<runtime-api-key>"
```

If environment variables are omitted, the UI sends the API Base URL and Runtime API key to the local server session. The key stays in process memory only and is not written to disk by this app.

## Quick Demo

1. Open the app and test connection.
2. Select `Payroll Operating Model`.
3. Confirm the role fields are prefilled for `Senior Payroll Specialist`.
4. Click `Create source and ingest`.
5. Click `Generate grounded report`.
6. Review summary, criteria, evidence, confidence, review flags, trace IDs, and snippets.
7. Fetch trace.
8. Delete the demo source.

## Evidence Gate

The app blocks report generation until source creation and ingestion are confirmed by API responses. A typed or prefilled source ID is not enough by itself. The app must confirm:

- source metadata exists for the authenticated tenant
- the source is active
- at least one ingestion run completed or was safely skipped as idempotent with indexed artifacts
- at least one artifact/document chunk exists for the source

If those checks are not met, the UI shows:

```text
Create and ingest a source before generating a grounded report.
```

A report response that has no evidence, no criteria, or the `missing_customer_grounding_evidence` review flag is rendered as an ungrounded fallback for debugging. It is not shown as a successful grounded demo.

## Local Smoke Helper

Run the smoke helper against a DEV/local backend with a Runtime API key whose contract allows `/api/v1/grounding`:

```powershell
$env:AVELIN_API_BASE = "http://127.0.0.1:8010"
$env:AVELIN_RUNTIME_API_KEY = "<runtime-api-key>"
$env:AVELIN_DEMO_EVIDENCE_DIR = "C:\_dev\avelin_runtime\evidence\customer_grounding_live_demo_evidence_flow_<timestamp>"
C:\programdata\anaconda3\envs\skillvista\python.exe smoke_live_demo.py
```

The helper creates a short-lived payroll sample source, ingests the bundled Markdown sample, refreshes ingestion status, generates a Role Intelligence report, asserts `evidence_count > 0`, fetches the trace when available, and deletes the source. If the backend returns zero evidence after successful ingestion, the helper exits non-zero and marks the demo smoke failed.
## Security

- Runtime API keys are never committed and should never be pasted into screenshots or issues.
- Customer/evaluator demos should use the one onboarding Runtime API key provided by AvelinLabs, pasted into the UI.
- `create_demo_runtime_key.py` is internal/local DEV-only, refuses non-localhost API bases, and prints the raw temporary key only once.
- The local proxy keeps the key in process memory only.
- The browser never calls AvelinLabs directly; it calls `localhost` routes under `/local-api/*`.
- The server binds to `127.0.0.1` by default and refuses non-localhost binding unless `--allow-non-localhost` is explicitly supplied.
- Server logging redacts common key and bearer-token patterns.
- Synthetic samples are safe demo content and are not customer data.

## Troubleshooting

- `401`: missing or invalid Runtime API key.
- `403`: key does not have contract allow-list access to `/api/v1/grounding`, or tenant context is unavailable. Ask AvelinLabs onboarding/provisioning to update or replace the onboarding key; do not create a separate DEV key for customer use.
- `404`: API Base URL is wrong, or the runtime route is unavailable on that server.
- CORS errors: use `server.py`; the browser should call the local proxy, not the runtime API directly.
- PDF ingestion: PDF must contain selectable text. OCR and image extraction are not supported.
- DOCX ingestion: paragraphs and straightforward tables are supported; macros and embedded objects are not parsed.
- File size: Customer Grounding file ingestion is capped by the backend controlled-beta limit.

## cURL Adoption

Create source:

```bash
curl -sS -X POST "$BASE_URL/api/v1/grounding/sources" \
  -H "Authorization: Bearer $AVELIN_API_KEY" \
  -H "Content-Type: application/json" \
  --data '{
    "source_id": "<SOURCE_ID>",
    "source_type": "customer_text",
    "title": "Customer Grounding Demo Source",
    "owner": "local-live-demo",
    "permissions_scope": "customer_private",
    "retention_class": "short_lived",
    "metadata": {"example": "customer-grounding-live-demo-app"}
  }'
```

Ingest text:

```bash
curl -sS -X POST "$BASE_URL/api/v1/grounding/sources/<SOURCE_ID>/ingest-text" \
  -H "Authorization: Bearer $AVELIN_API_KEY" \
  -H "Content-Type: application/json" \
  --data '{
    "content_type": "text/markdown",
    "version_label": "live-demo-text-v1",
    "text": "<SYNTHETIC_OR_APPROVED_CONTEXT>"
  }'
```

Generate report:

```bash
curl -sS -X POST "$BASE_URL/api/v1/grounding/role-intelligence/reports" \
  -H "Authorization: Bearer $AVELIN_API_KEY" \
  -H "Content-Type: application/json" \
  --data '{
    "role_title": "Senior Payroll Specialist",
    "role_context": "Multi-state payroll support, ADP Workforce Now, Excel reconciliation, and HR operations handoffs.",
    "focus_areas": ["multi-state payroll", "ADP Workforce Now", "review guidance"],
    "source_ids": ["<SOURCE_ID>"],
    "top_k": 5
  }'
```

## MCP Adoption

The current MCP adapter supports text/Markdown ingestion and maps to the same Runtime API contracts:

```json
[
  {
    "tool": "avelin_register_grounding_source",
    "arguments": {
      "source_id": "<SOURCE_ID>",
      "source_type": "customer_text",
      "title": "Customer Grounding Demo Source",
      "owner": "local-live-demo"
    }
  },
  {
    "tool": "avelin_ingest_grounding_text",
    "arguments": {
      "source_id": "<SOURCE_ID>",
      "content_type": "text/markdown",
      "version_label": "live-demo-text-v1",
      "text": "<SYNTHETIC_OR_APPROVED_CONTEXT>"
    }
  },
  {
    "tool": "avelin_generate_grounded_role_intelligence",
    "arguments": {
      "role_title": "Senior Payroll Specialist",
      "role_context": "Multi-state payroll support, ADP Workforce Now, Excel reconciliation, and HR operations handoffs.",
      "focus_areas": ["multi-state payroll", "ADP Workforce Now", "review guidance"],
      "source_ids": ["<SOURCE_ID>"],
      "top_k": 5
    }
  },
  {
    "tool": "avelin_get_grounding_trace",
    "arguments": {
      "trace_id": "<TRACE_ID>"
    }
  }
]
```

Use REST `ingest-file` for PDF, DOCX, Markdown, or TXT file uploads. The current MCP adapter does not upload files independently.

## Guardrails

- Do not include `customer_id` in bodies, query strings, or MCP tool input.
- Use synthetic or approved customer-provided content only.
- Treat generated output as human-in-the-loop decision support.
- Do not claim connectors, OCR, vector retrieval, SDK support, production GA, or hosted product UI from this local example.
