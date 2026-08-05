from __future__ import annotations

import os

import requests

from common import base_url, load_payload, print_json


def main() -> None:
    response = requests.post(
        f"{base_url()}/api/v1/job/classify",
        headers={
            "Accept": "application/json",
            "Authorization": "Bearer intentionally-invalid-example-key",
        },
        json=load_payload("job-classify.json"),
        timeout=30,
    )
    if response.status_code != 401:
        raise SystemExit(f"Expected HTTP 401, received {response.status_code}.")
    body = response.json()
    for field in ("detail", "request_id", "status_code"):
        if field not in body:
            raise SystemExit(f"Expected error field missing: {field}")
    print_json(body)


if __name__ == "__main__":
    main()
