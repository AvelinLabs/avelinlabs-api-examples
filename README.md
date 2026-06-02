# Avelinlabs API Examples

Public examples for the Avelinlabs Developer API.

Repository target:

https://github.com/AvelinLabs/avelinlabs-api-examples

## Beta / Early Access

Avelinlabs is currently in beta / early access. API surfaces, examples, response fields and documentation may evolve as the platform matures.

These examples are aligned with the current documented implementation in `backend/docs/`. They are intended to be minimal starting points, not a guarantee of production readiness or final API shape.

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
api-examples/
|-- README.md
|-- curl/
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

Platform onboarding and account endpoints are documented in backend docs, but full account lifecycle examples are not included here yet. Those flows involve registration, email verification, management bearer tokens and runtime API key creation, so examples should be added only when the public contract is verified for the target environment.

## cURL Examples

From the repository root:

```bash
export BASE_URL="https://api.avelinlabs.com"
export AVELIN_API_KEY="replace-with-your-key"

bash api-examples/curl/job-analyze.sh
bash api-examples/curl/job-classify.sh
bash api-examples/curl/occupation-profile.sh
bash api-examples/curl/market-top-us-technology.sh
bash api-examples/curl/health-ready.sh
```

The cURL examples keep payloads in `api-examples/payloads/` and pass the bearer token through the `Authorization` header where required.

## Python Examples

Install the only runtime dependency:

```bash
python -m pip install requests
```

Then run:

```bash
set BASE_URL=https://api.avelinlabs.com
set AVELIN_API_KEY=replace-with-your-key

python api-examples/python/job_analyze.py
python api-examples/python/job_classify.py
python api-examples/python/occupation_profile.py
python api-examples/python/market_top.py
python api-examples/python/health_ready.py
```

On macOS/Linux, use `export` instead of `set`.

## Payloads

Payload files are stored under `api-examples/payloads/`.

Current payloads:

- `job-analyze.json`
- `job-classify.json`

The request schema for `job/analyze` and `job/classify` is documented as:

- `title` (`string`, required)
- `description` (`string`, optional)
- `debug` (`boolean`, optional)

## Responses

Sample responses are stored under `api-examples/responses/`.

Some responses are copied from or closely aligned to backend documentation. Others are conservative illustrative examples where the docs describe the response concept but not an exact payload. Illustrative files include a `"_note"` field so they are not mistaken for guaranteed response contracts.

## Postman

A simple Postman collection is available at:

```text
api-examples/postman/avelinlabs-api.postman_collection.json
```

Configure these collection variables before use:

- `base_url`
- `avelin_api_key`

## Contract Notes

- Do not treat these examples as finalized API contracts.
- Public `/api/v1/*` paths are documented under additive-only governance for v0.1.
- Confidence-like fields are not all calibrated probabilities.
- Public product endpoints require customer runtime API keys.
- Management endpoints use management bearer tokens from login and are intentionally not expanded here yet.
