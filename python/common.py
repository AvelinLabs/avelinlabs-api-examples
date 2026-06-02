from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests


BASE_DIR = Path(__file__).resolve().parents[1]
PAYLOADS_DIR = BASE_DIR / "payloads"


def base_url() -> str:
    return os.environ.get("BASE_URL", "https://api.avelinlabs.com").rstrip("/")


def api_key(required: bool = True) -> str | None:
    value = os.environ.get("AVELIN_API_KEY")
    if required and not value:
        raise SystemExit("Set AVELIN_API_KEY before running this example.")
    return value


def load_payload(filename: str) -> dict[str, Any]:
    with (PAYLOADS_DIR / filename).open("r", encoding="utf-8") as file:
        return json.load(file)


def print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def request_json(method: str, path: str, *, payload: dict[str, Any] | None = None, auth: bool = True) -> Any:
    headers = {"Accept": "application/json"}
    token = api_key(required=auth)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        headers["Content-Type"] = "application/json"

    url = f"{base_url()}{path}"
    try:
        response = requests.request(method, url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
    except requests.HTTPError as exc:
        print(f"HTTP error calling {url}: {exc}")
        try:
            print_json(response.json())
        except ValueError:
            print(response.text)
        raise SystemExit(1) from exc
    except requests.RequestException as exc:
        raise SystemExit(f"Request failed calling {url}: {exc}") from exc

    try:
        return response.json()
    except ValueError:
        return {"raw_response": response.text}
