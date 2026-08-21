from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[1]
REQUEST_PATH = ROOT / "workforce-evidence-pack" / "request.json"
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", ROOT / "workforce-evidence-pack" / "output"))


def require_environment() -> tuple[str, str]:
    base_url = str(os.environ.get("BASE_URL") or "https://api.avelinlabs.com").rstrip("/")
    api_key = str(os.environ.get("AVELIN_API_KEY") or "")
    if not api_key:
        raise SystemExit("Set AVELIN_API_KEY to a Runtime API Key before running this example.")
    return base_url, api_key


def call(
    session: requests.Session,
    method: str,
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    accept: str = "application/json",
) -> requests.Response:
    response = session.request(
        method,
        url,
        json=payload,
        headers={"Accept": accept},
        timeout=30,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        print(f"HTTP {response.status_code} calling {url}")
        print(response.text)
        raise SystemExit(1) from exc
    return response


def main() -> None:
    base_url, api_key = require_environment()
    request_payload = json.loads(REQUEST_PATH.read_text(encoding="utf-8"))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with requests.Session() as session:
        session.headers.update({"Authorization": f"Bearer {api_key}"})

        capabilities = call(
            session,
            "GET",
            f"{base_url}/api/v1/workforce/capabilities?country_code=US",
        ).json()
        if capabilities["features"]["evidence_pack_creation"] != "available":
            raise SystemExit("Evidence Pack creation is not enabled for US in this environment.")

        occupations = call(
            session,
            "GET",
            f"{base_url}/api/v1/workforce/occupations?country_code=US&query=welder&limit=5",
        ).json()
        if not any(item["code"] == "51-4121" for item in occupations["items"]):
            raise SystemExit("The SOC help response did not contain 51-4121.")

        detail = call(
            session,
            "GET",
            f"{base_url}/api/v1/workforce/occupations/51-4121?country_code=US",
        ).json()
        if detail["code"] != "51-4121":
            raise SystemExit("Unexpected SOC detail response.")

        first_response = call(
            session,
            "POST",
            f"{base_url}/api/v1/workforce/evidence-packs",
            payload=request_payload,
        )
        first = first_response.json()

        reordered = dict(request_payload)
        reordered["industries"] = list(reversed(request_payload["industries"]))
        reordered["occupations"] = list(reversed(request_payload["occupations"]))
        second_response = call(
            session,
            "POST",
            f"{base_url}/api/v1/workforce/evidence-packs",
            payload=reordered,
        )
        second = second_response.json()

        pack_id = first["evidence_pack_id"]
        if second["evidence_pack_id"] != pack_id or second["cache_status"] != "reused":
            raise SystemExit("Deterministic cache reuse check failed.")

        document = call(
            session,
            "GET",
            f"{base_url}/api/v1/workforce/evidence-packs/{pack_id}",
        ).json()
        report = call(
            session,
            "GET",
            f"{base_url}/api/v1/workforce/evidence-packs/{pack_id}/report?format=html",
            accept="text/html",
        ).text

    if document["evidence_pack_id"] != pack_id or "<!doctype html>" not in report.lower():
        raise SystemExit("Evidence Pack retrieval validation failed.")

    json_path = OUTPUT_DIR / f"{pack_id}.json"
    html_path = OUTPUT_DIR / f"{pack_id}.html"
    json_path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    html_path.write_text(report, encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "passed",
                "evidence_pack_id": pack_id,
                "first_http_status": first_response.status_code,
                "first_cache_status": first["cache_status"],
                "second_http_status": second_response.status_code,
                "cache_reused": True,
                "occupations": len(document["evidence"]["occupations"]),
                "industries": len(document["evidence"]["industries"]),
                "json_path": str(json_path),
                "html_path": str(html_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
