from __future__ import annotations

import getpass
import os
from typing import Any

import requests


def base_url() -> str:
    return os.environ.get("BASE_URL", "https://api.avelinlabs.com").rstrip("/")


def call(method: str, path: str, *, payload: dict[str, Any] | None = None, token: str | None = None) -> dict[str, Any]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.request(
        method,
        f"{base_url()}{path}",
        headers=headers,
        json=payload,
        timeout=30,
    )
    try:
        body = response.json()
    except ValueError:
        body = {"detail": response.text, "status_code": response.status_code}
    if not response.ok:
        request_id = body.get("request_id") or response.headers.get("X-Request-ID") or "unavailable"
        raise SystemExit(f"HTTP {response.status_code}: {body.get('detail', body)} (request_id={request_id})")
    return body


def required(name: str, prompt: str) -> str:
    value = os.environ.get(name, "").strip() or input(prompt).strip()
    if not value:
        raise SystemExit(f"{name} is required.")
    return value


def main() -> None:
    email = required("AVELIN_EMAIL", "Email: ")
    password = os.environ.get("AVELIN_PASSWORD") or getpass.getpass("Password: ")

    register = input("Register this account now? [Y/n]: ").strip().lower() not in {"n", "no"}
    if register:
        full_name = required("AVELIN_FULL_NAME", "Full name: ")
        company_name = required("AVELIN_COMPANY_NAME", "Company name: ")
        result = call(
            "POST",
            "/api/v1/platform/register",
            payload={
                "email": email,
                "password": password,
                "full_name": full_name,
                "company_name": company_name,
            },
        )
        print(result.get("message", "Registration submitted."))

    token = os.environ.get("AVELIN_VERIFICATION_TOKEN", "").strip()
    if not token:
        token = input("Paste the verification token from the email, or press Enter if already verified: ").strip()
    if token:
        result = call("GET", f"/api/v1/platform/verify-email?token={requests.utils.quote(token, safe='')}")
        print(result.get("message", "Email verified."))

    login = call("POST", "/api/v1/platform/login", payload={"email": email, "password": password})
    management_token = str(login["access_token"])

    key_name = os.environ.get("AVELIN_KEY_NAME", "local-development").strip() or "local-development"
    created = call(
        "POST",
        "/api/v1/platform/api-keys/create",
        payload={"name": key_name},
        token=management_token,
    )
    raw_api_key = created.get("raw_api_key")
    if not raw_api_key:
        raise SystemExit("The key response did not include raw_api_key.")

    print("\nRuntime API Key (shown once; store it securely):")
    print(raw_api_key)
    print("\nDo not commit this value or use the management token on Runtime endpoints.")


if __name__ == "__main__":
    main()
