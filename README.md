# Avelinlabs API Examples

Public examples for the Avelinlabs Developer API.

Repository target:

https://github.com/AvelinLabs/avelinlabs-api-examples

## Beta / Early Access

Avelinlabs is currently in beta / early access. API surfaces, examples, response fields and documentation may evolve as the platform matures.

These examples are aligned with the current public beta API documentation. They are intended to be minimal starting points, not a guarantee of production readiness or final API shape.

## Base URL

Use the public API base URL for hosted access:

```text
https://api.avelinlabs.com
```

All examples allow overriding the base URL:

```bash
export BASE_URL="https://api.avelinlabs.com"
```

## Authentication

Protected product/runtime endpoints use bearer authentication:

```http
Authorization: Bearer <AVELIN_API_KEY>
```

Set your API key as an environment variable:

```bash
export AVELIN_API_KEY="replace-with-your-key"
```

Public liveness/readiness endpoints (`/health/live`, `/health/ready`) are anonymous.

## Repository Structure

```text
.
|-- README.md
|-- curl/
|-- docs/
|-- python/
|-- payloads/
|-- responses/
`-- postman/
```

## Covered Endpoints

The examples cover documented public product and health surfaces:

- `POST /api/v1/job/analyze`
- `POST /api/v1/job/classify`
- `GET /api/v1/occupation/{onet_code}`
- `GET /api/v1/occupation/profile/{onet_code}`
- `GET /api/v1/market/top`
- `GET /api/v1/market/skills/trending`
- `GET /api/v1/market/technologies/trending`
- `GET /api/v1/market/overview`
- `GET /api/v1/market/remote-rate`
- `GET /health/live`
- `GET /health/ready`

Platform onboarding and account endpoints are described in the public API documentation, but full account lifecycle examples are not included here yet. Those flows involve registration, email verification, management bearer tokens and runtime API key creation, so executable examples should be added only when the public contract is verified for the target environment.

## cURL Examples

From the repository root:

```bash
export BASE_URL="https://api.avelinlabs.com"
export AVELIN_API_KEY="replace-with-your-key"

bash curl/job-analyze.sh
bash curl/job-classify.sh
bash curl/occupation-profile.sh
bash curl/market-top-us-technology.sh
bash curl/health-ready.sh
```

The cURL examples keep payloads in `payloads/` and pass the bearer token through the `Authorization` header where required. Scripts that send payload files resolve the repository root from the script location, so they can be run from the repository root without a nested `api-examples/` path.

## Python Examples

Install the only runtime dependency:

```bash
python -m pip install requests
```

Then run:

```bash
set BASE_URL=https://api.avelinlabs.com
set AVELIN_API_KEY=replace-with-your-key

python python/job_analyze.py
python python/job_analyze_summary.py
python python/job_classify.py
python python/occupation_profile.py
python python/market_top.py
python python/health_ready.py
```

On macOS/Linux, use `export` instead of `set`.

## Payloads

Payload files are stored under `payloads/`.

Current payloads:

- `job-analyze.json`
- `job-classify.json`
- `hr-service-role-intake.json`

The request schema for `job/analyze` and `job/classify` is documented as:

- `title` (`string`, required)
- `description` (`string`, optional)
- `debug` (`boolean`, optional)

## Responses

Sample responses are stored under `responses/`.

Some responses are copied from or closely aligned to backend documentation. Others are conservative illustrative examples where the docs describe the response concept but not an exact payload. Illustrative files include a `"_note"` field so they are not mistaken for guaranteed response contracts.

## Response Interpretation

The annotated job analysis response guide is available at:

```text
docs/annotated-job-analyze-response.md
```

It explains the fields in `responses/job-analyze.example.json` in plain English for business and technical evaluators.

## Postman

A simple Postman collection is available at:

```text
postman/avelinlabs-api.postman_collection.json
```

Configure these collection variables before use:

- `base_url`
- `avelin_api_key`

## Contract Notes

- Do not treat these examples as finalized API contracts.
- Public `/api/v1/*` paths are documented under additive-only governance for v0.1.
- Current occupation intelligence is grounded in O*NET 30.3. Market `technology` examples use the public API category name and may represent software-oriented terms in the current reference model.
- Confidence-like fields are not all calibrated probabilities.
- Public product endpoints require customer runtime API keys.
- Management endpoints use management bearer tokens from login and are intentionally not expanded here yet.
