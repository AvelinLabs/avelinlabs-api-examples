from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

APP_DIR = Path(__file__).resolve().parent
SAMPLE_PATH = APP_DIR / "samples" / "payroll-operating-model.md"
SUCCESSFUL_RUN_STATUSES = {"completed", "skipped"}


class SmokeFailure(RuntimeError):
    pass


def parse_sample(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    metadata: dict[str, Any] = {}
    body = text
    if text.startswith("---\n"):
        _start, rest = text.split("---\n", 1)
        frontmatter, body = rest.split("---\n", 1)
        for line in frontmatter.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            raw = value.strip().strip('"')
            metadata[key.strip()] = [item.strip() for item in raw.split(",") if item.strip()] if key.strip() == "focus_areas" else raw
    metadata["content"] = body.strip()
    return metadata


def call_api(base_url: str, api_key: str, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = Request(f"{base_url.rstrip('/')}{path}", data=body, method=method, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            return parse_response(response.read())
    except HTTPError as exc:
        response = parse_response(exc.read())
        raise SmokeFailure(f"{method} {path} failed with HTTP {exc.code}: {safe_json(response)}") from exc
    except URLError as exc:
        raise SmokeFailure(f"{method} {path} failed: {exc.reason}") from exc


def parse_response(data: bytes) -> dict[str, Any]:
    if not data:
        return {}
    parsed = json.loads(data.decode("utf-8"))
    return parsed if isinstance(parsed, dict) else {"response": parsed}


def write_json(evidence_dir: Path, name: str, payload: dict[str, Any]) -> None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / name).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def safe_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True)[:1200]


def evidence_count(payload: dict[str, Any]) -> int:
    seen: set[str] = set()
    for item in [*(payload.get("evidence_references") or []), *(payload.get("evidence_snapshots") or [])]:
        key = str(item.get("evidence_id") or f"{item.get('source_id')}:{item.get('artifact_id')}")
        if key:
            seen.add(key)
    return len(seen)


def successful_ingestion_run(runs: list[dict[str, Any]]) -> dict[str, Any] | None:
    for run in runs:
        if run.get("status") in SUCCESSFUL_RUN_STATUSES and int(run.get("artifact_count") or 0) > 0:
            return run
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke test the Customer Grounding live demo evidence flow.")
    parser.add_argument("--base-url", default=os.getenv("AVELIN_API_BASE", "http://127.0.0.1:8010"))
    parser.add_argument("--api-key", default=os.getenv("AVELIN_RUNTIME_API_KEY", ""))
    parser.add_argument("--evidence-dir", default=os.getenv("AVELIN_DEMO_EVIDENCE_DIR", ""))
    parser.add_argument("--keep-source", action="store_true", help="Do not delete the smoke source at the end.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.api_key:
        print(
            "No Runtime API key configured. Create a DEV-only demo key with: "
            "python create_demo_runtime_key.py --dev-mode local --env-file <backend-env-file> create --ttl-hours 4",
            file=sys.stderr,
        )
        return 2

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    source_id = f"cg-live-smoke-payroll-{timestamp}"
    evidence_dir = Path(args.evidence_dir) if args.evidence_dir else APP_DIR / "evidence" / f"customer_grounding_live_demo_evidence_flow_{timestamp}"
    sample = parse_sample(SAMPLE_PATH)
    summary: dict[str, Any] = {
        "status": "started",
        "base_url": args.base_url,
        "source_id": source_id,
        "evidence_dir": str(evidence_dir),
        "steps": [],
    }
    source_created = False

    try:
        capabilities = call_api(args.base_url, args.api_key, "GET", "/api/v1/grounding/capabilities")
        write_json(evidence_dir, "01_capabilities.json", capabilities)
        summary["steps"].append("capabilities")

        create_payload = {
            "source_id": source_id,
            "source_type": "customer_text",
            "title": sample.get("title") or "Payroll Operating Model",
            "owner": "local-live-demo-smoke",
            "permissions_scope": "customer_private",
            "retention_class": "short_lived",
            "metadata": {"example": "customer-grounding-live-demo-app", "smoke": True},
        }
        created = call_api(args.base_url, args.api_key, "POST", "/api/v1/grounding/sources", create_payload)
        source_created = True
        write_json(evidence_dir, "02_create_source.json", created)
        summary["steps"].append("create_source")

        ingest_payload = {
            "text": sample["content"],
            "content_type": "text/markdown",
            "version_label": "live-demo-smoke-text-v1",
            "metadata": {"example": "customer-grounding-live-demo-app", "smoke": True},
        }
        ingested = call_api(args.base_url, args.api_key, "POST", f"/api/v1/grounding/sources/{quote(source_id, safe='')}/ingest-text", ingest_payload)
        write_json(evidence_dir, "03_ingest_text.json", ingested)
        summary["steps"].append("ingest_text")

        source_status = call_api(args.base_url, args.api_key, "GET", f"/api/v1/grounding/sources/{quote(source_id, safe='')}")
        write_json(evidence_dir, "04_source_status.json", source_status)
        runs_payload = call_api(args.base_url, args.api_key, "GET", f"/api/v1/grounding/sources/{quote(source_id, safe='')}/ingestion-runs?limit=20")
        write_json(evidence_dir, "05_ingestion_runs.json", runs_payload)
        runs = list(runs_payload.get("ingestion_runs") or [])
        run = successful_ingestion_run(runs)
        if source_status.get("source", {}).get("status") != "active" or run is None:
            raise SmokeFailure("Source did not become active with a successful ingestion run.")
        summary["steps"].append("verify_ingestion")

        report_payload = {
            "role_title": sample.get("suggested_role_title") or "Senior Payroll Specialist",
            "role_context": "\n\n".join(
                item
                for item in [sample.get("suggested_role_context"), f"Business question: {sample.get('suggested_business_question')}"]
                if item
            ),
            "focus_areas": sample.get("focus_areas") or [],
            "source_ids": [source_id],
            "top_k": 5,
        }
        report = call_api(args.base_url, args.api_key, "POST", "/api/v1/grounding/role-intelligence/reports", report_payload)
        write_json(evidence_dir, "06_report.json", report)
        count = evidence_count(report)
        summary["evidence_count"] = count
        summary["trace_id"] = report.get("trace_id") or report.get("trace", {}).get("trace_id")
        summary["decision_id"] = report.get("trace", {}).get("decision_id")
        summary["steps"].append("generate_report")
        if count <= 0:
            raise SmokeFailure("No grounding evidence was returned. Demo smoke failed.")

        if summary.get("trace_id"):
            trace = call_api(args.base_url, args.api_key, "GET", f"/api/v1/grounding/traces/{quote(str(summary['trace_id']), safe='')}")
            write_json(evidence_dir, "07_trace.json", trace)
            summary["trace_evidence_count"] = len(trace.get("evidence_snapshots") or [])
            summary["steps"].append("fetch_trace")

        summary["status"] = "passed"
        return 0
    except SmokeFailure as exc:
        summary["status"] = "failed"
        summary["error"] = str(exc)
        return 1
    finally:
        if source_created and not args.keep_source:
            try:
                cleanup = call_api(
                    args.base_url,
                    args.api_key,
                    "DELETE",
                    f"/api/v1/grounding/sources/{quote(source_id, safe='')}",
                    {"reason": "customer grounding live demo smoke cleanup"},
                )
                write_json(evidence_dir, "08_cleanup.json", cleanup)
                summary["cleanup_status"] = cleanup.get("source", {}).get("status")
                summary["steps"].append("cleanup_source")
            except SmokeFailure as exc:
                summary["cleanup_status"] = "failed"
                summary["cleanup_error"] = str(exc)
        write_json(evidence_dir, "summary.json", summary)
        print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
