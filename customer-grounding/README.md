# Customer Grounding Controlled Beta Examples

These examples show the current Customer Grounding controlled-beta REST API and local MCP stdio adapter model.

They do not claim production GA, connectors, OCR, image extraction, vector/hybrid retrieval, SDK wrappers, a full UI, a hosted MCP daemon, or automated hiring decisions.

## Authentication

Set a Runtime API Key whose contract allows `/api/v1/grounding`:

```bash
export BASE_URL="https://api.avelinlabs.com"
export AVELIN_API_KEY="replace-with-your-runtime-api-key"
```

On Windows PowerShell:

```powershell
$env:BASE_URL = "https://api.avelinlabs.com"
$env:AVELIN_API_KEY = "replace-with-your-runtime-api-key"
```

Do not put raw keys in committed files.

Current quotas, retained-document limits, and storage limits are maintained in the [public Customer Grounding documentation](https://avelinlabs.com/docs/customer-grounding/). This repository links to that source of truth instead of duplicating values that may evolve.

## Supported File Formats

The current public file-ingestion route supports only:

| Format | Extension | MIME type |
| --- | --- | --- |
| Text | `.txt`, `.text` | `text/plain` |
| Markdown | `.md`, `.markdown` | `text/markdown` |
| PDF | `.pdf` | `application/pdf` |
| DOCX | `.docx` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |

PDF support is selectable text only. DOCX support extracts paragraphs and straightforward table text. DOCX macros and embedded objects are rejected. Maximum upload size is `5242880` bytes.

## REST Workflow

Python:

```bash
python customer-grounding/python/customer_grounding_workflow.py
```

cURL:

```bash
bash customer-grounding/curl/customer-grounding-workflow.sh
```

Optional negative file-validation examples:

```bash
RUN_NEGATIVE_CASES=1 python customer-grounding/python/customer_grounding_workflow.py
bash customer-grounding/curl/file-validation-errors.sh
```

The REST workflow covers:

- register source
- list sources
- get source
- ingest text/Markdown
- ingest `.txt`, `.md`, `.pdf`, and `.docx`
- list versions
- list artifacts
- retrieve ingestion run
- generate grounded Role Intelligence report
- retrieve trace
- disable source
- enable source
- delete source
- customer_id rejection
- file validation errors
- oversized-file error
- corrupt-file error

Saved response provenance and fixture classification are documented in `responses/README.md`; no Customer Grounding file in that directory is presented as a live production result.

## Endpoint guide

Every endpoint below requires a Runtime API Key whose contract permits `/api/v1/grounding`. Tenant scope comes from that credential; never add `customer_id` to a request.

| Endpoint | What it provides | Important fields, limits, and behavior |
| --- | --- | --- |
| `GET /api/v1/grounding/capabilities` | Returns the capabilities and limits available to the authenticated account. | Treat returned limits as authoritative for that account and environment. |
| `POST /api/v1/grounding/sources` | Registers a tenant-scoped evidence source. | `title` is required; `source_id`, `source_type`, `owner`, `permissions_scope`, `retention_class`, and `metadata` are optional. |
| `GET /api/v1/grounding/sources` | Lists sources visible to the authenticated tenant. | Results are tenant-scoped and may change as sources are enabled, disabled, or deleted. |
| `GET /api/v1/grounding/sources/{source_id}` | Returns one tenant-scoped source. | A source created with another account must not be visible. |
| `POST /api/v1/grounding/sources/{source_id}/ingest-text` | Creates a source version and ingestion run from text. | `text` is required (1-20,000 characters); `content_type`, `version_label`, and `metadata` are optional. |
| `POST /api/v1/grounding/sources/{source_id}/ingest-file` | Ingests TXT, Markdown, selectable-text PDF, or DOCX as multipart form data. | `file` is required; `version_label` and JSON metadata are optional. The public route limit is 5 MiB; OCR, macros, and embedded objects are not supported. |
| `GET /api/v1/grounding/sources/{source_id}/versions` | Lists retained versions for a source. | Version and retention details are response data, not values clients should invent. |
| `GET /api/v1/grounding/sources/{source_id}/artifacts` | Lists derived artifacts for a source. | Artifacts remain tenant-scoped and traceable to the source/version lifecycle. |
| `GET /api/v1/grounding/ingestion-runs/{ingestion_run_id}` | Retrieves one ingestion run. | Use the identifier returned by ingestion; do not assume IDs or completion timing. |
| `POST /api/v1/grounding/role-intelligence/reports` | Builds a grounded Role Intelligence report from active tenant evidence. | `role_title` is required; `role_context` is optional up to 10,000 characters; `focus_areas` and `source_ids` accept at most 20 items; `top_k` is 1-20 and defaults to 5. |
| `GET /api/v1/grounding/traces/{trace_id}` | Retrieves the decision trace for a generated report. | Use the returned `trace_id`; traces are evidence for review, not final hiring decisions. |
| `POST /api/v1/grounding/sources/{source_id}/disable` | Excludes a source from active grounding without deleting it. | The optional action body is empty; lifecycle changes affect later reports. |
| `POST /api/v1/grounding/sources/{source_id}/enable` | Restores a disabled source to active grounding. | The optional action body is empty. |
| `DELETE /api/v1/grounding/sources/{source_id}` | Deletes the source through the documented lifecycle. | An optional `reason` can be supplied. The examples use best-effort cleanup after failures. |

## Tenant Isolation

Do not send `customer_id`. The Runtime API derives tenant scope from the authenticated platform account context. Requests with `customer_id` in JSON, query string, multipart form fields, or file metadata are rejected.

To validate tenant isolation, use two temporary Runtime API Keys from different controlled-beta accounts. A source, version, artifact, ingestion run, report, or trace created with one key must not be visible with the other key.

## MCP Examples

The MCP adapter is a customer-operated local stdio adapter over the authenticated Runtime API. It is not a separate Avelin-hosted MCP server.

Current MCP tools expose text ingestion only. Use REST for file ingestion.

See:

```text
customer-grounding/mcp/client-config.example.json
customer-grounding/mcp/stdio-launch.md
customer-grounding/mcp/tool-calls.example.json
```

## Offline Validation

Validate JSON, Python examples, and sample files:

```bash
python customer-grounding/validate_examples.py
```

The validator checks JSON syntax, Python compilation, text/Markdown UTF-8, PDF structure, DOCX package structure, file sizes, and that sample DOCX files do not contain macro or embedded-object members.
