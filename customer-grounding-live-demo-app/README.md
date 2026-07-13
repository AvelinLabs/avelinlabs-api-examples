# Customer Grounding Live Demo App

A local, interactive example of AvelinLabs Customer Grounding.

The app lets evaluators add customer context, generate grounded Role Intelligence, inspect supporting evidence and traceability, and then remove the temporary demo source.

It is an API-first and MCP-first adoption example. It is not a hosted production UI or a final hiring decision tool.

## What the demo shows

- Customer-specific context ingestion from text, Markdown, PDF, DOCX, or TXT.
- Grounded Role Intelligence generated from confirmed source content.
- Evidence-backed findings with excerpts and source references.
- Confidence, uncertainty, and human-review flags.
- A human-readable trace of the generated result.
- Copyable REST and MCP adoption examples.
- Safe cleanup of temporary demo sources.

## Prerequisites

- Python 3.10 to 3.12.
- An AvelinLabs API Base URL.
- A Runtime API key provided by AvelinLabs with access to Customer Grounding.

## Start the app

From the repository root:

~~~bash
cd customer-grounding-live-demo-app
python server.py --host 127.0.0.1 --port 8765
~~~

On Windows, py can be used instead:

~~~powershell
cd customer-grounding-live-demo-app
py -3 server.py --host 127.0.0.1 --port 8765
~~~

Open:

~~~text
http://127.0.0.1:8765/
~~~

## Connect from the dashboard

Enter the following values in the Runtime connection panel:

1. The API Base URL supplied for the evaluation.
2. The Runtime API key supplied by AvelinLabs.
3. Select Save connection.
4. Select Test connection.

The dashboard is the standard customer and evaluator configuration path. No environment variable or local configuration file is required.

The key is kept only in the local server process memory. It is not written to repository files, browser localStorage, or browser sessionStorage. The browser sends requests only to the local proxy, which calls the configured AvelinLabs API.

## Recommended demo flow

1. Save and test the connection.
2. Select Payroll Operating Model.
3. Review the prefilled Senior Payroll Specialist request.
4. Select Prepare grounded context.
5. Wait until the dashboard confirms that the customer context is ready.
6. Select Generate grounded intelligence.
7. Review the summary, criteria, evidence, confidence, and review flags.
8. Select Review trace.
9. Select Remove demo context.

## Evidence gate

Report generation remains disabled until the API confirms that:

- the selected source exists for the authenticated tenant;
- the source is active;
- ingestion completed successfully or was safely skipped as idempotent;
- at least one document artifact is available.

A response without evidence, without grounded criteria, or with the missing_customer_grounding_evidence review flag is shown as an ungrounded fallback. It is not presented as a successful grounded result.

## Included synthetic samples

- Payroll Operating Model
- Customer Success Renewal Playbook
- Manufacturing Quality Role Framework

The bundled samples contain synthetic content and can be used without customer data.

## File ingestion

The dashboard accepts:

- PDF with selectable text;
- DOCX containing paragraphs and straightforward tables;
- Markdown;
- plain text.

OCR, macros, embedded objects, and image extraction are not supported by this example. Backend-controlled upload limits still apply.

## API and MCP adoption

The dashboard includes copyable examples for:

- registering a source;
- ingesting text;
- generating grounded Role Intelligence;
- retrieving a trace.

REST supports both text and approved file ingestion. The current MCP example supports text and Markdown ingestion and maps to the same Customer Grounding runtime contracts.

## Security and usage guardrails

- Use only synthetic content or customer-provided content approved for the evaluation.
- Do not include customer_id in request bodies, query strings, or MCP input. Tenant context is derived from authentication.
- Do not include Runtime API keys in screenshots, documentation, tickets, or committed files.
- Keep the server bound to 127.0.0.1 for normal evaluator use.
- Treat generated output as human-in-the-loop decision support.
- Do not present the example as a hosted product UI or production GA capability.

## Troubleshooting

- 401: the Runtime API key is missing or invalid.
- 403: the key does not allow Customer Grounding access, or tenant context is unavailable.
- 404: the API Base URL is incorrect, or Customer Grounding is unavailable on that server.
- Browser CORS error: access the API through this local app rather than calling the runtime API directly from another page.
- Report generation remains disabled: verify that source creation and ingestion completed and that at least one artifact was indexed.

For onboarding or access problems, contact AvelinLabs rather than creating an additional local key.
