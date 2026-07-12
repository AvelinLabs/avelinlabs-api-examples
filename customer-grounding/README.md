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
