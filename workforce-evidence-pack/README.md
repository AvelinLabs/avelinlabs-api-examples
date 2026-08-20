# Workforce Evidence Pack controlled-beta example

This example exercises the complete authenticated Workforce API lifecycle:

1. discover capabilities;
2. search and retrieve U.S. SOC help;
3. create or reuse a Connecticut Workforce Evidence Pack;
4. prove order-independent deterministic cache reuse;
5. retrieve the account-scoped JSON document;
6. save the standalone HTML buyer report.

The endpoint packages approved OEWS occupation evidence, separate Census QWI
industry-flow evidence, and governed O*NET 30.3 task and skill reference data.
It does not rank occupations, infer NAICS from SOC, make an investment
recommendation, or call JobDataAPI during the request.

## Availability

This surface is controlled beta and may not yet be enabled in production. Set
`BASE_URL` explicitly to an environment whose
`GET /api/v1/workforce/capabilities?country_code=US` response advertises
`features.evidence_pack_creation=available`.

The committed request is intentionally bounded to `US / state / CT`. The
renderer is reusable, but this example is not evidence that arbitrary countries
or regions have approved official snapshots.

## Occupation and industry identifiers

- `occupations` contains six-digit 2018 SOC codes such as `51-4121`.
- `industries` contains NAICS codes such as `311` and `334`.
- SOC, O*NET-SOC, and NAICS are different taxonomies and remain separate.

See the official [BLS Standard Occupational Classification site](https://www.bls.gov/soc/)
for the U.S. SOC standard. Use the Workforce occupation-help endpoints to list
the bounded Avelin/O*NET 30.3 reference details accepted by the API.

## Python

From the repository root:

```bash
python3 -m pip install -r requirements.txt
export BASE_URL="http://127.0.0.1:8010"
export AVELIN_API_KEY="replace-with-your-runtime-api-key"
python3 python/workforce_evidence_pack.py
```

Windows:

```powershell
py -3 -m pip install -r requirements.txt
$env:BASE_URL = "http://127.0.0.1:8010"
$env:AVELIN_API_KEY = "replace-with-your-runtime-api-key"
py -3 python\workforce_evidence_pack.py
```

## Native PowerShell

```powershell
$env:BASE_URL = "http://127.0.0.1:8010"
$env:AVELIN_API_KEY = "replace-with-your-runtime-api-key"
.\powershell\workforce-evidence-pack.ps1
```

Both workflows save the retrieved JSON and HTML under
`workforce-evidence-pack/output/` by default. Set `OUTPUT_DIR` to use another
location. Do not commit customer-generated output or credentials.

## cURL creation request

```bash
curl --fail-with-body --silent --show-error \
  -X POST "$BASE_URL/api/v1/workforce/evidence-packs" \
  -H "Authorization: Bearer $AVELIN_API_KEY" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  --data @workforce-evidence-pack/request.json
```

On PowerShell use `curl.exe` explicitly.

## Buyer-facing fixture

`reports/connecticut-manufacturing.example.html` is the accepted static buyer
example created from the Issue #285/#290 Connecticut evidence fixture. It is a
GitHub-viewable product example and renderer reference, not a live API response,
production observation, or arbitrary-country availability claim.

## Expected gate

The workflow succeeds only when it confirms:

- Evidence Pack creation is advertised;
- SOC help returns `51-4121`;
- two order-equivalent requests return the same `evidence_pack_id`;
- the second response reports `cache_status=reused`;
- JSON and standalone HTML retrieval both succeed.

JobDataAPI remains `HOLD` and no provider subscription is required.
