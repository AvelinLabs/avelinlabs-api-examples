from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests


EXAMPLE_ROOT = Path(__file__).resolve().parents[1]
REQUESTS_DIR = EXAMPLE_ROOT / "requests"
SAMPLE_FILES_DIR = EXAMPLE_ROOT / "sample-files"
MAX_FILE_BYTES = 5 * 1024 * 1024


def base_url() -> str:
    return os.environ.get("BASE_URL", "https://api.avelinlabs.com").rstrip("/")


def api_key() -> str:
    value = os.environ.get("AVELIN_API_KEY", "").strip()
    if not value:
        raise SystemExit("Set AVELIN_API_KEY before running this example.")
    return value


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def print_json(label: str, payload: Any) -> None:
    print(f"\n## {label}")
    print(json.dumps(payload, indent=2, sort_keys=True))


class GroundingClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_key()}",
                "Accept": "application/json",
            }
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        json_payload: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        data: dict[str, str] | None = None,
        expect_error: bool = False,
    ) -> Any:
        url = f"{base_url()}{path}"
        response = self.session.request(
            method,
            url,
            json=json_payload,
            files=files,
            data=data,
            timeout=30,
        )
        if not expect_error:
            response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            return {"status_code": response.status_code, "text": response.text}

    def upload_file(self, source_id: str, filename: str, media_type: str, version_label: str) -> Any:
        path = SAMPLE_FILES_DIR / filename
        with path.open("rb") as file:
            return self.request(
                "POST",
                f"/api/v1/grounding/sources/{source_id}/ingest-file",
                files={"file": (path.name, file, media_type)},
                data={"version_label": version_label},
            )


def run_workflow() -> None:
    client = GroundingClient()
    source_id = os.environ.get("SOURCE_ID", f"synthetic-role-criteria-{os.getpid()}")

    print_json("capabilities", client.request("GET", "/api/v1/grounding/capabilities"))

    register_payload = load_json(REQUESTS_DIR / "register-source.json")
    register_payload["source_id"] = source_id
    print_json("register source", client.request("POST", "/api/v1/grounding/sources", json_payload=register_payload))
    print_json("list sources", client.request("GET", "/api/v1/grounding/sources"))
    print_json("get source", client.request("GET", f"/api/v1/grounding/sources/{source_id}"))

    text_result = client.request(
        "POST",
        f"/api/v1/grounding/sources/{source_id}/ingest-text",
        json_payload=load_json(REQUESTS_DIR / "ingest-text.json"),
    )
    print_json("ingest text", text_result)

    file_specs = [
        ("synthetic-role-criteria.txt", "text/plain", "synthetic-txt-v1"),
        ("synthetic-role-criteria.md", "text/markdown", "synthetic-md-v1"),
        ("synthetic-role-criteria.pdf", "application/pdf", "synthetic-pdf-v1"),
        (
            "synthetic-role-criteria.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "synthetic-docx-v1",
        ),
    ]
    for filename, media_type, version_label in file_specs:
        print_json(f"ingest file {filename}", client.upload_file(source_id, filename, media_type, version_label))

    print_json("list versions", client.request("GET", f"/api/v1/grounding/sources/{source_id}/versions"))
    print_json("list artifacts", client.request("GET", f"/api/v1/grounding/sources/{source_id}/artifacts"))

    ingestion_run_id = text_result["ingestion_run"]["ingestion_run_id"]
    print_json("get ingestion run", client.request("GET", f"/api/v1/grounding/ingestion-runs/{ingestion_run_id}"))

    report = client.request(
        "POST",
        "/api/v1/grounding/role-intelligence/reports",
        json_payload=load_json(REQUESTS_DIR / "role-intelligence-report.json"),
    )
    print_json("generate report", report)

    trace_id = report["trace_id"]
    print_json("get trace", client.request("GET", f"/api/v1/grounding/traces/{trace_id}"))
    print_json("disable source", client.request("POST", f"/api/v1/grounding/sources/{source_id}/disable", json_payload={}))
    print_json("enable source", client.request("POST", f"/api/v1/grounding/sources/{source_id}/enable", json_payload={}))

    if os.environ.get("RUN_NEGATIVE_CASES") == "1":
        run_negative_examples(client, source_id)

    print_json(
        "delete source",
        client.request(
            "DELETE",
            f"/api/v1/grounding/sources/{source_id}",
            json_payload=load_json(REQUESTS_DIR / "delete-source.json"),
        ),
    )


def run_negative_examples(client: GroundingClient, source_id: str) -> None:
    print_json(
        "customer_id rejection",
        client.request(
            "POST",
            f"/api/v1/grounding/sources/{source_id}/ingest-text",
            json_payload=load_json(REQUESTS_DIR / "customer-id-rejection.json"),
            expect_error=True,
        ),
    )
    print_json(
        "corrupt pdf rejection",
        client.request(
            "POST",
            f"/api/v1/grounding/sources/{source_id}/ingest-file",
            files={"file": ("corrupt.pdf", b"not a pdf", "application/pdf")},
            expect_error=True,
        ),
    )
    print_json(
        "oversized file rejection",
        client.request(
            "POST",
            f"/api/v1/grounding/sources/{source_id}/ingest-file",
            files={"file": ("oversized.txt", b"x" * (MAX_FILE_BYTES + 1), "text/plain")},
            expect_error=True,
        ),
    )


if __name__ == "__main__":
    run_workflow()
