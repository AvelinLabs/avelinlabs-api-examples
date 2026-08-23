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
It does not rank occupations, infer NAICS from SOC, or make an investment
recommendation.

## Availability

This surface is live in production as a controlled beta for authenticated,
entitled callers using the approved U.S./Connecticut snapshot. The examples
default to `https://api.avelinlabs.com`; override `BASE_URL` only for an approved
DEV or staging environment. Always confirm that
`GET /api/v1/workforce/capabilities?country_code=US` advertises
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
export BASE_URL="https://api.avelinlabs.com"
export AVELIN_API_KEY="replace-with-your-runtime-api-key"
python3 python/workforce_evidence_pack.py
```

Windows:

```powershell
py -3 -m pip install -r requirements.txt
$env:BASE_URL = "https://api.avelinlabs.com"
$env:AVELIN_API_KEY = "replace-with-your-runtime-api-key"
py -3 python\workforce_evidence_pack.py
```

## Native PowerShell

```powershell
$env:BASE_URL = "https://api.avelinlabs.com"
$env:AVELIN_API_KEY = "replace-with-your-runtime-api-key"
.\powershell\workforce-evidence-pack.ps1
```

Both workflows save the retrieved JSON and HTML under
`workforce-evidence-pack/output/` by default. Set `OUTPUT_DIR` to use another
location. Do not commit customer-generated output or credentials.

## cURL lifecycle

The cURL examples cover capability discovery, SOC search/detail, pack creation,
JSON retrieval, and HTML retrieval:

```bash
export BASE_URL="https://api.avelinlabs.com"
export AVELIN_API_KEY="replace-with-your-runtime-api-key"

bash curl/workforce-capabilities.sh
bash curl/workforce-occupations.sh
bash curl/workforce-occupation.sh
bash curl/workforce-evidence-pack.sh

export EVIDENCE_PACK_ID="wep_copy_the_id_returned_by_creation"
bash curl/workforce-evidence-pack-get.sh
bash curl/workforce-evidence-pack-report.sh
```

The report script writes `${EVIDENCE_PACK_ID}.html` under
`workforce-evidence-pack/output/`. On PowerShell use `curl.exe` explicitly, or
run the native PowerShell lifecycle above.

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

