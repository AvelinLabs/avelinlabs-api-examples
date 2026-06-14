from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import PAYLOADS_DIR, request_json


DEFAULT_PAYLOAD = "job-analyze.json"


def load_payload_arg(value: str) -> dict[str, Any]:
    path = Path(value)
    if not path.is_absolute():
        if len(path.parts) == 1:
            path = PAYLOADS_DIR / value
        else:
            path = Path.cwd() / path

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def join_names(values: list[Any], limit: int = 5) -> str:
    names = [str(value) for value in values if value]
    return ", ".join(names[:limit]) if names else "None reported"


def review_guidance(result: dict[str, Any]) -> str:
    decision = result.get("decision", {})
    label = decision.get("decision")
    confidence = result.get("confidence")
    uncertainty = result.get("uncertainty", {}).get("total")

    if label == "AUTO_ACCEPT":
        return "Candidate for low-risk automatic use if your workflow policy allows it."
    if label in {"REVIEW", "AMBIGUOUS"}:
        return "Send to a reviewer or consultant before using in a client-facing recommendation."
    if label == "REJECT":
        return "Do not use for automation; request clearer job input or review manually."
    if isinstance(confidence, (int, float)) and isinstance(uncertainty, (int, float)):
        if confidence >= 0.75 and uncertainty <= 0.25:
            return "Strong signal, but apply your own review policy before automation."
    return "Review according to your workflow policy, especially if the input is vague or overlapping."


def print_summary(result: dict[str, Any]) -> None:
    first_result = next(iter(as_list(result.get("results"))), {})
    decision = result.get("decision", {})
    explanation = first_result.get("explanation", {})

    print(f"Job title: {result.get('job_title', 'Unknown')}")
    print(
        "Top match: "
        f"{first_result.get('title', 'Unknown')} ({first_result.get('onet_code', 'unknown code')})"
    )
    print(f"Confidence: {result.get('confidence', 'n/a')} / {result.get('confidence_level', 'n/a')}")
    print(f"Trust score: {result.get('trust_score', 'n/a')}")
    print(f"Decision: {decision.get('decision', 'n/a')}")
    print(f"Decision reason: {decision.get('reason', 'n/a')}")
    print(f"Key signals: {join_names(as_list(result.get('job_signals')))}")
    print(f"Matching skills: {join_names(as_list(first_result.get('matching_skills')))}")
    print(f"Why match: {explanation.get('why_match', 'No explanation returned.')}")
    print(f"Review guidance: {review_guidance(result)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Call POST /api/v1/job/analyze and print a business-friendly summary."
    )
    parser.add_argument(
        "payload",
        nargs="?",
        default=DEFAULT_PAYLOAD,
        help=(
            "Payload file to send. Use a path such as payloads/hr-service-role-intake.json, "
            "or a file name from the payloads directory. Defaults to payloads/job-analyze.json."
        ),
    )
    args = parser.parse_args()

    payload = load_payload_arg(args.payload)
    result = request_json("POST", "/api/v1/job/analyze", payload=payload)
    print_summary(result)


if __name__ == "__main__":
    main()
