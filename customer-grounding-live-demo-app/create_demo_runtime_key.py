from __future__ import annotations

import argparse
import os
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parents[1]
BACKEND_DIR = REPO_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from environment_bootstrap import ensure_environment_loaded  # noqa: E402

ensure_environment_loaded()

from application.services.platform_security import (  # noqa: E402
    generate_api_key,
    hash_api_key,
    hash_password,
    mask_api_key,
)
from infrastructure.database.platform_connection import (  # noqa: E402
    get_platform_db_config,
    platform_db_enabled,
    platform_inmemory_enabled,
)
from infrastructure.database.platform_repository import (  # noqa: E402
    PlatformAuditRecord,
    get_platform_repository,
    utcnow,
)
from skillvista.branding import get_env_bool, get_env_value  # noqa: E402


DEFAULT_API_BASE = "http://127.0.0.1:8010"
DEFAULT_SCOPE = "/api/v1/grounding"
DEMO_EMAIL = "customer-grounding-live-demo@avelinlabs.local"
DEMO_FULL_NAME = "Customer Grounding Live Demo"
DEMO_COMPANY = "AvelinLabs DEV Customer Grounding Demo"
DEMO_CONTRACT_TYPE = "grounding_demo"
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
PRODUCTION_MARKERS = {"prod", "production", "live"}


class BootstrapError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or revoke a DEV-only Customer Grounding Runtime API key.",
    )
    parser.add_argument(
        "--base-url",
        default=str(get_env_value("API_BASE", get_env_value("API_URL", DEFAULT_API_BASE)) or DEFAULT_API_BASE),
        help="Target local DEV backend URL used as a safety guard. Defaults to AVELIN_API_BASE or localhost.",
    )
    parser.add_argument(
        "--dev-mode",
        choices=("local", "development"),
        required=True,
        help="Required explicit acknowledgement that this helper is running only against local/development.",
    )
    parser.add_argument(
        "--env-file",
        default="",
        help="Optional local backend .env file to load before create/revoke. Values are never printed.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create", help="Create a temporary Customer Grounding Runtime API key.")
    create.add_argument(
        "--scope",
        default=DEFAULT_SCOPE,
        help="Runtime route scope. This DEV helper only allows /api/v1/grounding.",
    )
    create.add_argument(
        "--ttl-hours",
        type=int,
        default=4,
        help="Key expiration in hours. Must be between 1 and 24.",
    )
    create.add_argument(
        "--key-name",
        default="Customer Grounding live demo temporary key",
        help="Non-secret key label stored with the Runtime API key.",
    )
    create.add_argument(
        "--email",
        default=DEMO_EMAIL,
        help="Synthetic .local demo user email to create or reuse.",
    )

    revoke = subparsers.add_parser("revoke", help="Revoke a temporary Customer Grounding Runtime API key by id.")
    revoke.add_argument("--key-id", type=int, required=True, help="Platform ApiKeys.ApiKeyId to revoke.")

    return parser.parse_args()


def require_dev_only(args: argparse.Namespace) -> None:
    if get_env_bool("STRICT_PRODUCTION_MODE", False):
        raise BootstrapError("Refusing to run because strict production mode is enabled.")
    runtime_marker = first_env_value("ENVIRONMENT", "APP_ENV", "ENV", "RUNTIME_ENVIRONMENT")
    if runtime_marker and runtime_marker.strip().lower() in PRODUCTION_MARKERS:
        raise BootstrapError(f"Refusing to run because environment marker is {runtime_marker!r}.")
    if not is_local_base_url(str(args.base_url)):
        raise BootstrapError("Refusing to run because --base-url is not localhost/127.0.0.1/[::1].")
    if str(args.dev_mode).strip().lower() not in {"local", "development"}:
        raise BootstrapError("Pass --dev-mode local or --dev-mode development to acknowledge DEV-only use.")


def first_env_value(*names: str) -> str:
    for name in names:
        value = str(get_env_value(name, "") or "").strip()
        if value:
            return value
    return ""


def load_env_file(path_value: str) -> None:
    if not str(path_value or "").strip():
        return
    path = Path(path_value).expanduser().resolve()
    if not path.is_file():
        raise BootstrapError(f"Env file was not found: {path}")
    normalized = str(path).lower()
    if normalized.startswith("c:\\_prod\\"):
        raise BootstrapError("Refusing to load an env file from C:\\_prod.")
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key.startswith(("AVELIN_", "SKILLVISTA_")) and key != "API_KEY":
            continue
        os.environ[key] = value.strip().strip('"').strip("'")


def is_local_base_url(value: str) -> bool:
    parsed = urlparse(str(value or ""))
    if parsed.scheme not in {"http", "https"}:
        return False
    return str(parsed.hostname or "").lower() in LOCAL_HOSTS


def require_grounding_scope(scope: str) -> str:
    normalized = str(scope or "").strip().rstrip("/")
    if normalized != DEFAULT_SCOPE:
        raise BootstrapError("This DEV helper only creates keys scoped to /api/v1/grounding.")
    return DEFAULT_SCOPE


def require_ttl_hours(value: int) -> int:
    ttl_hours = int(value)
    if ttl_hours < 1 or ttl_hours > 24:
        raise BootstrapError("--ttl-hours must be between 1 and 24.")
    return ttl_hours


def get_repository():
    if platform_inmemory_enabled():
        raise BootstrapError(
            "Platform in-memory mode is process-local and cannot bootstrap a key for a separate backend. "
            "Use the SQL-backed local DEV platform database used by the running backend."
        )
    repository = get_platform_repository()
    if repository is None:
        config = get_platform_db_config()
        mode = "sqlserver" if platform_db_enabled() else "unconfigured"
        configured_hint = "configured" if config.is_configured else "not configured"
        raise BootstrapError(
            "Platform repository is unavailable. "
            f"Mode={mode}; platform DB is {configured_hint}. "
            "Load the local DEV platform DB environment used by the backend before running this helper."
        )
    return repository


def get_or_create_demo_user(repository, email: str):
    normalized_email = str(email or "").strip().lower()
    if not normalized_email.endswith(".local"):
        raise BootstrapError("Synthetic demo user email must end in .local.")

    user = repository.get_user_by_email(normalized_email)
    if user is None:
        user = repository.create_user(
            email=normalized_email,
            password_hash=hash_password(secrets.token_urlsafe(32)),
            full_name=DEMO_FULL_NAME,
            company_name=DEMO_COMPANY,
            role="customer",
            status="active",
            demo_requested=False,
        )
        user = repository.update_user(
            user.user_id,
            full_name=DEMO_FULL_NAME,
            company_name=DEMO_COMPANY,
            role="customer",
            status="active",
            is_email_verified=True,
            demo_requested=False,
        )
        return user, True

    updated = repository.update_user(
        user.user_id,
        full_name=user.full_name or DEMO_FULL_NAME,
        company_name=user.company_name or DEMO_COMPANY,
        role="customer",
        status="active",
        is_email_verified=True,
        demo_requested=False,
    )
    return updated, False


def record_audit(repository, *, action: str, target_type: str, target_id: str, details: dict[str, Any]) -> None:
    try:
        repository.record_audit(
            PlatformAuditRecord(
                actor_user_id=None,
                actor_email="customer-grounding-demo-key-bootstrap@avelinlabs.local",
                action=action,
                target_type=target_type,
                target_id=target_id,
                details=details,
            )
        )
    except Exception:
        # Audit logging must not cause the helper to print sensitive values or fail after key creation.
        pass


def create_key(args: argparse.Namespace) -> int:
    require_dev_only(args)
    scope = require_grounding_scope(args.scope)
    ttl_hours = require_ttl_hours(args.ttl_hours)
    repository = get_repository()

    now = utcnow()
    expires_at = now + timedelta(hours=ttl_hours)
    user, created_user = get_or_create_demo_user(repository, args.email)
    contract = repository.create_contract(
        user_id=user.user_id,
        account_id=user.account_id,
        contract_type=DEMO_CONTRACT_TYPE,
        status="trial",
        requests_per_minute=120,
        daily_quota=250,
        concurrent_requests=4,
        max_payload_bytes=262144,
        enabled_endpoints=[scope],
        auto_approve_demo=False,
        starts_at=now,
        ends_at=expires_at,
    )
    raw_key, prefix = generate_api_key()
    api_key = repository.create_api_key(
        user_id=user.user_id,
        contract_id=contract.contract_id,
        key_name=str(args.key_name).strip() or "Customer Grounding live demo temporary key",
        key_prefix=prefix,
        key_hash=hash_api_key(raw_key),
        masked_preview=mask_api_key(raw_key),
        expires_at=expires_at,
    )
    record_audit(
        repository,
        action="dev.customer_grounding_demo_key.create",
        target_type="api_key",
        target_id=str(api_key.api_key_id),
        details={
            "contract_id": contract.contract_id,
            "user_id": user.user_id,
            "account_id": user.account_id,
            "created_user": created_user,
            "enabled_endpoints": [scope],
            "expires_at": expires_at.isoformat(),
            "dev_only": True,
        },
    )

    print("DEV-ONLY Customer Grounding Runtime API key created.")
    print("Use this key only against a local/development backend. Do not paste it into docs, screenshots, tickets, or commits.")
    print("")
    print(f"Runtime API key (copy once): {raw_key}")
    print(f"Key id: {api_key.api_key_id}")
    print(f"Masked preview: {api_key.masked_preview}")
    print(f"Contract id: {contract.contract_id}")
    print(f"Account id: {user.account_id}")
    print(f"Scope: {scope}")
    print(f"Expires at UTC: {expires_at.isoformat()}")
    print("")
    print('PowerShell: $env:AVELIN_RUNTIME_API_KEY = "<printed-key>"')
    print(f"Revoke: python create_demo_runtime_key.py --dev-mode {args.dev_mode} revoke --key-id {api_key.api_key_id}")
    return 0


def revoke_key(args: argparse.Namespace) -> int:
    require_dev_only(args)
    repository = get_repository()
    api_key = repository.get_api_key(args.key_id)
    if api_key is None:
        raise BootstrapError(f"API key id {args.key_id} was not found.")
    contract = repository.get_contract(api_key.contract_id)
    if contract is None or list(contract.enabled_endpoints or []) != [DEFAULT_SCOPE]:
        raise BootstrapError("Refusing to revoke because the key is not attached to a /api/v1/grounding-only demo contract.")
    updated = repository.update_api_key(api_key.api_key_id, status="revoked", revoked_at=utcnow())
    record_audit(
        repository,
        action="dev.customer_grounding_demo_key.revoke",
        target_type="api_key",
        target_id=str(updated.api_key_id),
        details={
            "contract_id": updated.contract_id,
            "enabled_endpoints": contract.enabled_endpoints,
            "dev_only": True,
        },
    )
    revoked_at = updated.revoked_at or datetime.now(timezone.utc)
    print("DEV-ONLY Customer Grounding Runtime API key revoked.")
    print(f"Key id: {updated.api_key_id}")
    print(f"Status: {updated.status}")
    print(f"Revoked at UTC: {revoked_at.isoformat()}")
    return 0


def main() -> int:
    args = parse_args()
    try:
        load_env_file(args.env_file)
        if args.command == "create":
            return create_key(args)
        if args.command == "revoke":
            return revoke_key(args)
        raise BootstrapError(f"Unsupported command: {args.command}")
    except BootstrapError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
