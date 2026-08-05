# AvelinLabs API Examples

Runnable examples for the public AvelinLabs Platform and Runtime APIs.

- Documentation: https://avelinlabs.com/docs/
- Getting started: https://avelinlabs.com/docs/getting-started/
- API reference: https://avelinlabs.com/docs/api/
- Machine-readable OpenAPI 3.1 contract: https://api.avelinlabs.com/openapi.json
- Production base URL: `https://api.avelinlabs.com`

AvelinLabs is in public beta. The public v1 contract follows additive-only evolution; clients should ignore unknown response fields and avoid depending on debug-only fields.

## Five-minute Runtime quickstart

Clone the repository, install the single Python dependency, set a Runtime API Key, and run a request.

### Bash (macOS/Linux)

```bash
git clone https://github.com/AvelinLabs/avelinlabs-api-examples.git
cd avelinlabs-api-examples
python3 -m pip install -r requirements.txt
export BASE_URL="https://api.avelinlabs.com"
export AVELIN_API_KEY="replace-with-your-runtime-api-key"
python3 python/job_classify.py
```

### Windows PowerShell

```powershell
git clone https://github.com/AvelinLabs/avelinlabs-api-examples.git
Set-Location avelinlabs-api-examples
py -3 -m pip install -r requirements.txt
$env:BASE_URL = "https://api.avelinlabs.com"
$env:AVELIN_API_KEY = "replace-with-your-runtime-api-key"
py -3 python/job_classify.py
```

Native PowerShell example:

```powershell
.\powershell\job-classify.ps1
```

Use `Invoke-RestMethod` in native PowerShell scripts. When copying a cURL example into PowerShell, call `curl.exe` explicitly so the command does not depend on PowerShell alias behavior.

### Windows Command Prompt

```bat
git clone https://github.com/AvelinLabs/avelinlabs-api-examples.git
cd avelinlabs-api-examples
py -3 -m pip install -r requirements.txt
set "BASE_URL=https://api.avelinlabs.com"
set "AVELIN_API_KEY=replace-with-your-runtime-api-key"
py -3 python\job_classify.py
```

Command Prompt wrappers are under `cmd/`.

## Create an account and Runtime API Key

The public self-service flow is:

1. register;
2. verify the email address;
3. log in to receive a management bearer token;
4. create a Runtime API Key;
5. use the Runtime API Key on product endpoints.

Management bearer tokens and Runtime API Keys are different credentials. Never use the login token on Runtime product routes.

Python:

```bash
python3 python/platform_onboarding.py
```

PowerShell:

```powershell
.\powershell\platform-onboarding.ps1
```

Command Prompt:

```bat
cmd\platform-onboarding.cmd
```

The raw Runtime API Key is returned once. The examples do not persist it automatically.

## Authentication

Protected Runtime endpoints use:

```http
Authorization: Bearer <runtime-api-key>
```

`GET /health/live` and `GET /health/ready` are public and anonymous.

## Coverage

| Area | Python | Bash/cURL | PowerShell/CMD | Postman |
| --- | --- | --- | --- | --- |
| Platform onboarding | `platform_onboarding.py` | docs flow | native PowerShell and CMD wrapper | register, verify, login, key creation |
| Job analyze/classify | yes | yes | native classify; all Python scripts run from both shells | yes |
| Occupation candidates/summary/profile | yes | yes | run the Python scripts from either Windows shell | yes |
| Market top/overview | yes | yes | run the Python scripts from either Windows shell | yes |
| Market skill/technology trends | yes | yes | native PowerShell and CMD wrappers | yes |
| Market remote rate | yes | yes | native PowerShell and CMD wrapper | yes |
| Health live/ready | yes | yes | native PowerShell and CMD wrappers | yes |
| Customer Grounding | full lifecycle | full lifecycle | Python workflow runs from both Windows shells | lifecycle collection |
| Standard 401 error | executable | response fixture | executable through Python | tested request |

## Runtime examples

From Bash:

```bash
bash curl/job-analyze.sh
bash curl/job-classify.sh
bash curl/occupation-candidates.sh
bash curl/occupation.sh
bash curl/occupation-profile.sh
bash curl/market-top-us-technology.sh
bash curl/market-overview.sh
bash curl/market-skills-trending.sh
bash curl/market-technologies-trending.sh
bash curl/market-remote-rate.sh
bash curl/health-live.sh
bash curl/health-ready.sh
```

From Python on macOS/Linux:

```bash
python3 python/job_analyze.py
python3 python/job_classify.py
python3 python/occupation_candidates.py
python3 python/occupation.py
python3 python/occupation_profile.py
python3 python/market_top.py
python3 python/market_overview.py
python3 python/market_skills_trending.py
python3 python/market_technologies_trending.py
python3 python/market_remote_rate.py
python3 python/health_live.py
python3 python/health_ready.py
```

On Windows replace `python3` with `py -3`.

## Input quality evaluation

Executable payloads are under `input-quality/`:

- strong job description;
- title-only input;
- vague input;
- ambiguous role;
- noisy or non-occupational input.

Use them to inspect confidence, uncertainty, ambiguity, weak-signal detection, decision routing, skills, and explanations. Do not expect fixed numerical confidence values.

## Error handling

Run the standard invalid-key example:

```bash
python3 python/error_invalid_api_key.py
```

It verifies HTTP `401` and the public error envelope fields:

- `detail`
- `request_id`
- `status_code`

The Postman collection contains the equivalent test.

## Customer Grounding

The full controlled-beta lifecycle is under `customer-grounding/` and covers:

- capabilities;
- source registration and lifecycle;
- text, Markdown, TXT, selectable-text PDF, and DOCX ingestion;
- versions, artifacts, and ingestion runs;
- grounded Role Intelligence;
- evidence and decision traces;
- negative file and tenant-isolation cases;
- cleanup.

Python:

```bash
python3 customer-grounding/python/customer_grounding_workflow.py
```

Bash:

```bash
bash customer-grounding/curl/customer-grounding-workflow.sh
```

Both workflows perform best-effort cleanup if a later request fails. Current quotas, retention limits, and file limits are maintained in the [Customer Grounding documentation](https://avelinlabs.com/docs/customer-grounding/) so this repository does not duplicate values that may evolve.

## Responses

Response fixtures are stored under `responses/`. Read `responses/README.md` before using them.

Illustrative fixtures:

- are not guaranteed production snapshots;
- use placeholders where a runtime value should not be invented;
- contain only response fields, not repository metadata such as `_note`;
- should be validated against the public OpenAPI contract.

`AUTO_ACCEPT` is a routing signal for low-risk workflow handling where customer policy permits it. It is not a final hiring decision.

## Postman

Import:

```text
postman/avelinlabs-api.postman_collection.json
```

Configure the collection variables before use. The collection groups Platform, Job, Occupation, Market, Health, Customer Grounding, and Errors. It does not automatically persist the one-time raw Runtime API Key.

## Repository structure

```text
.
|-- cmd/
|-- curl/
|-- customer-grounding/
|-- customer-grounding-live-demo-app/
|-- docs/
|-- input-quality/
|-- payloads/
|-- postman/
|-- powershell/
|-- python/
|-- responses/
|-- requirements.txt
`-- README.md
```

## Contract and safety notes

- Current occupation intelligence uses O*NET 30.3.
- Occupation candidate rank 1 is a suggestion, not an official mapping.
- Market counts, percentages, and growth values are scoped signals, not universal totals.
- Confidence-like fields are not interchangeable calibrated probabilities.
- Treat submitted text and outputs as customer data.
- Never commit API keys, management tokens, verification tokens, passwords, customer documents, or raw production payloads.
- Consequential workforce decisions remain human-led.
