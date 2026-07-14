from __future__ import annotations

import argparse
import cgi
import json
import mimetypes
import os
import re
import sys
import uuid
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, unquote, urlparse
from urllib.request import Request, urlopen

APP_DIR = Path(__file__).resolve().parent
SAMPLES_DIR = APP_DIR / "samples"
MAX_JSON_BYTES = 1_000_000
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}

SESSION: dict[str, str] = {
    "base_url": os.getenv("AVELIN_API_BASE", "https://api.avelinlabs.com").strip().rstrip("/"),
    "api_key": os.getenv("AVELIN_RUNTIME_API_KEY", "").strip(),
}

SECRET_PATTERNS = [
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]+", re.IGNORECASE),
    re.compile(r"avln_[A-Za-z0-9._\-]+", re.IGNORECASE),
    re.compile(r"sk-[A-Za-z0-9._\-]+", re.IGNORECASE),
]


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        sensitive_keys = {"api_key", "runtime_api_key", "authorization", "password", "secret", "token"}
        return {key: ("[REDACTED]" if key.lower() in sensitive_keys else redact(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        text = value
        for pattern in SECRET_PATTERNS:
            text = pattern.sub("[REDACTED]", text)
        key = SESSION.get("api_key") or ""
        if key:
            text = text.replace(key, "[REDACTED]")
        return text
    return value


def public_config() -> dict[str, Any]:
    api_key = SESSION.get("api_key") or ""
    return {
        "base_url": SESSION.get("base_url") or "",
        "api_key_configured": bool(api_key),
        "api_key_preview": f"...{api_key[-4:]}" if len(api_key) >= 4 else None,
        "storage": "process_memory_only",
    }


def parse_sample(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    metadata: dict[str, Any] = {"sample_id": path.stem, "filename": path.name}
    body = text
    if text.startswith("---\n"):
        _start, rest = text.split("---\n", 1)
        frontmatter, body = rest.split("---\n", 1)
        for line in frontmatter.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            normalized = key.strip()
            raw = value.strip().strip('"')
            if normalized in {"focus_areas"}:
                metadata[normalized] = [item.strip() for item in raw.split(",") if item.strip()]
            else:
                metadata[normalized] = raw
    metadata["content"] = body.strip()
    metadata.setdefault("title", path.stem.replace("-", " ").title())
    metadata.setdefault("suggested_role_title", "")
    metadata.setdefault("suggested_role_context", "")
    metadata.setdefault("suggested_business_question", "")
    metadata.setdefault("why_grounding_matters", "")
    metadata.setdefault("focus_areas", [])
    return metadata


def list_samples() -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    preferred_order = {
        "payroll-operating-model": 0,
        "customer-success-renewal-playbook": 1,
        "manufacturing-quality-role-framework": 2,
    }
    paths = sorted(SAMPLES_DIR.glob("*.md"), key=lambda item: (preferred_order.get(item.stem, 99), item.name))
    for path in paths:
        item = parse_sample(path)
        samples.append({key: value for key, value in item.items() if key != "content"})
    return samples


def sample_detail(sample_id: str) -> dict[str, Any]:
    safe_id = re.sub(r"[^a-zA-Z0-9_.-]", "", sample_id)
    path = SAMPLES_DIR / f"{safe_id}.md"
    if not path.exists():
        raise KeyError(sample_id)
    return parse_sample(path)


class LocalDemoHandler(SimpleHTTPRequestHandler):
    server_version = "AvelinCustomerGroundingLiveDemo/1.0"

    def translate_path(self, path: str) -> str:
        parsed = urlparse(path)
        relative = unquote(parsed.path.lstrip("/")) or "index.html"
        candidate = (APP_DIR / relative).resolve()
        if APP_DIR not in candidate.parents and candidate != APP_DIR:
            return str(APP_DIR / "index.html")
        return str(candidate)

    def log_message(self, fmt: str, *args: Any) -> None:
        message = redact(fmt % args)
        sys.stderr.write(f"[customer-grounding-live-demo] {message}\n")

    def do_GET(self) -> None:  # noqa: N802
        self._route("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._route("POST")

    def do_DELETE(self) -> None:  # noqa: N802
        self._route("DELETE")

    def _route(self, method: str) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        try:
            if path.startswith("/local-api"):
                self._local_api(method, path, parsed.query)
                return
            if method != "GET":
                self._send_json(HTTPStatus.METHOD_NOT_ALLOWED, {"error": "method_not_allowed"})
                return
            super().do_GET()
        except Exception as exc:  # defensive local-only error boundary
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": "local_demo_error", "detail": redact(str(exc))},
            )

    def _local_api(self, method: str, path: str, query: str) -> None:
        if method == "GET" and path == "/local-api/health":
            self._send_json(HTTPStatus.OK, {"status": "ok", "config": public_config()})
            return
        if method == "POST" and path == "/local-api/session":
            payload = self._read_json()
            base_url = str(payload.get("base_url") or "").strip().rstrip("/")
            api_key = str(payload.get("runtime_api_key") or payload.get("api_key") or "").strip()
            if base_url:
                parsed = urlparse(base_url)
                if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_base_url"})
                    return
                SESSION["base_url"] = base_url
            if api_key:
                SESSION["api_key"] = api_key
            self._send_json(HTTPStatus.OK, {"config": public_config()})
            return
        if method == "GET" and path == "/local-api/samples":
            self._send_json(HTTPStatus.OK, {"samples": list_samples()})
            return
        if method == "GET" and path.startswith("/local-api/samples/"):
            sample_id = unquote(path.rsplit("/", 1)[-1])
            try:
                self._send_json(HTTPStatus.OK, {"sample": sample_detail(sample_id)})
            except KeyError:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "sample_not_found"})
            return
        if method == "GET" and path == "/local-api/capabilities":
            self._proxy_json("GET", "/api/v1/grounding/capabilities")
            return
        if method == "POST" and path == "/local-api/sources":
            self._proxy_json("POST", "/api/v1/grounding/sources", self._read_json())
            return
        if method == "POST" and path == "/local-api/ingest-text":
            payload = self._read_json()
            source_id = require_text(payload, "source_id")
            upstream = {
                "text": require_text(payload, "text"),
                "content_type": str(payload.get("content_type") or "text/markdown"),
            }
            if payload.get("version_label"):
                upstream["version_label"] = str(payload["version_label"])
            if isinstance(payload.get("metadata"), dict):
                upstream["metadata"] = payload["metadata"]
            self._proxy_json("POST", f"/api/v1/grounding/sources/{quote(source_id, safe='')}/ingest-text", upstream)
            return
        if method == "POST" and path == "/local-api/ingest-file":
            self._proxy_file_upload()
            return
        if method == "POST" and path == "/local-api/reports":
            self._proxy_json("POST", "/api/v1/grounding/role-intelligence/reports", self._read_json())
            return
        if method == "GET" and path == "/local-api/usage":
            self._proxy_json("GET", "/api/v1/grounding/usage")
            return
        if method == "GET" and path.startswith("/local-api/traces/"):
            trace_id = unquote(path.rsplit("/", 1)[-1])
            self._proxy_json("GET", f"/api/v1/grounding/traces/{quote(trace_id, safe='')}")
            return
        if method == "GET" and path.startswith("/local-api/reports/"):
            decision_id = unquote(path.rsplit("/", 1)[-1])
            self._proxy_json("GET", f"/api/v1/grounding/reports/{quote(decision_id, safe='')}")
            return
        if method == "GET" and path.startswith("/local-api/sources/") and path.endswith("/readiness"):
            source_id = unquote(path.split("/")[3])
            self._send_source_readiness(source_id)
            return
        if method == "GET" and path.startswith("/local-api/sources/") and path.endswith("/artifacts"):
            source_id = unquote(path.split("/")[3])
            self._proxy_json("GET", f"/api/v1/grounding/sources/{quote(source_id, safe='')}/artifacts")
            return
        if method == "GET" and path.startswith("/local-api/sources/") and path.endswith("/ingestion-runs"):
            source_id = unquote(path.split("/")[3])
            params = parse_qs(query)
            limit = params.get("limit", ["50"])[0]
            self._proxy_json("GET", f"/api/v1/grounding/sources/{quote(source_id, safe='')}/ingestion-runs?limit={quote(limit)}")
            return
        if method == "GET" and path.startswith("/local-api/sources/"):
            source_id = unquote(path.rsplit("/", 1)[-1])
            self._proxy_json("GET", f"/api/v1/grounding/sources/{quote(source_id, safe='')}")
            return
        if method == "GET" and path.startswith("/local-api/ingestion-runs/"):
            run_id = unquote(path.rsplit("/", 1)[-1])
            self._proxy_json("GET", f"/api/v1/grounding/ingestion-runs/{quote(run_id, safe='')}")
            return
        if method == "POST" and path.startswith("/local-api/sources/") and path.endswith("/disable"):
            source_id = unquote(path.split("/")[3])
            self._proxy_json("POST", f"/api/v1/grounding/sources/{quote(source_id, safe='')}/disable", {})
            return
        if method == "DELETE" and path.startswith("/local-api/sources/"):
            source_id = unquote(path.rsplit("/", 1)[-1])
            payload = self._read_json(allow_empty=True) or {}
            self._proxy_json("DELETE", f"/api/v1/grounding/sources/{quote(source_id, safe='')}", payload)
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "local_api_route_not_found", "path": path})

    def _read_json(self, *, allow_empty: bool = False) -> dict[str, Any]:
        length = int(self.headers.get("content-length") or "0")
        if length <= 0:
            if allow_empty:
                return {}
            raise ValueError("JSON body is required")
        if length > MAX_JSON_BYTES:
            raise ValueError("JSON body is too large")
        data = self.rfile.read(length)
        return json.loads(data.decode("utf-8"))

    def _proxy_json(self, method: str, api_path: str, payload: dict[str, Any] | None = None) -> None:
        body = None
        headers: dict[str, str] = {}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        status, response = call_upstream(method, api_path, body=body, extra_headers=headers)
        self._send_json(status, response)

    def _send_source_readiness(self, source_id: str) -> None:
        encoded_source_id = quote(source_id, safe="")
        source_status, source_payload = call_upstream("GET", f"/api/v1/grounding/sources/{encoded_source_id}")
        if int(source_status) >= 400:
            self._send_json(source_status, {**source_payload, "readiness_step": "source"})
            return
        runs_status, runs_payload = call_upstream("GET", f"/api/v1/grounding/sources/{encoded_source_id}/ingestion-runs?limit=20")
        if int(runs_status) >= 400:
            self._send_json(runs_status, {**runs_payload, "readiness_step": "ingestion_runs"})
            return
        artifacts_status, artifacts_payload = call_upstream("GET", f"/api/v1/grounding/sources/{encoded_source_id}/artifacts")
        if int(artifacts_status) >= 400:
            self._send_json(artifacts_status, {**artifacts_payload, "readiness_step": "artifacts"})
            return
        self._send_json(
            HTTPStatus.OK,
            {
                "source": source_payload.get("source"),
                "ingestion_runs": runs_payload.get("ingestion_runs") or [],
                "artifacts": artifacts_payload.get("artifacts") or [],
            },
        )

    def _proxy_file_upload(self) -> None:
        content_length = int(self.headers.get("content-length") or "0")
        if content_length > MAX_UPLOAD_BYTES + 100_000:
            self._send_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "upload_too_large"})
            return
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": self.headers.get("content-type", ""),
                "CONTENT_LENGTH": str(content_length),
            },
        )
        source_id = str(form.getvalue("source_id") or "").strip()
        if not source_id:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "source_id_required"})
            return
        file_item = form["file"] if "file" in form else None
        if file_item is None or not getattr(file_item, "filename", None):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "file_required"})
            return
        file_data = file_item.file.read()
        if len(file_data) > MAX_UPLOAD_BYTES:
            self._send_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "upload_too_large"})
            return
        filename = Path(file_item.filename).name
        content_type = file_item.type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
        fields = {
            "version_label": str(form.getvalue("version_label") or "live-demo-file-v1"),
        }
        metadata_json = str(form.getvalue("metadata_json") or "").strip()
        if metadata_json:
            fields["metadata_json"] = metadata_json
        boundary, body = build_multipart(fields, filename=filename, content_type=content_type, file_data=file_data)
        status, response = call_upstream(
            "POST",
            f"/api/v1/grounding/sources/{quote(source_id, safe='')}/ingest-file",
            body=body,
            extra_headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        self._send_json(status, response)

    def _send_json(self, status: int | HTTPStatus, payload: dict[str, Any]) -> None:
        encoded = json.dumps(redact(payload), indent=2).encode("utf-8")
        self.send_response(int(status))
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)
        self.close_connection = True


def require_text(payload: dict[str, Any], key: str) -> str:
    value = str(payload.get(key) or "").strip()
    if not value:
        raise ValueError(f"{key} is required")
    return value


def call_upstream(
    method: str,
    api_path: str,
    *,
    body: bytes | None = None,
    extra_headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any]]:
    base_url = (SESSION.get("base_url") or "").rstrip("/")
    api_key = SESSION.get("api_key") or ""
    if not base_url or not api_key:
        return HTTPStatus.BAD_REQUEST, {
            "error": "not_configured",
            "detail": "Set backend URL and Runtime API key before calling live AvelinLabs APIs.",
            "offline_preview_only": True,
        }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    headers.update(extra_headers or {})
    request = Request(f"{base_url}{api_path}", data=body, method=method.upper(), headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            return response.status, parse_response(response.read())
    except HTTPError as exc:
        return exc.code, parse_response(exc.read(), fallback={"detail": exc.reason})
    except URLError as exc:
        return HTTPStatus.BAD_GATEWAY, {"error": "upstream_unreachable", "detail": str(exc.reason)}


def parse_response(data: bytes, *, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    if not data:
        return fallback or {}
    text = data.decode("utf-8", errors="replace")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"raw_response": text[:5000]}
    return parsed if isinstance(parsed, dict) else {"response": parsed}


def build_multipart(
    fields: dict[str, str],
    *,
    filename: str,
    content_type: str,
    file_data: bytes,
) -> tuple[str, bytes]:
    boundary = f"----avelin-live-demo-{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        chunks.append(str(value).encode("utf-8"))
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}\r\n".encode("utf-8"))
    safe_filename = filename.replace('"', "")
    chunks.append(f'Content-Disposition: form-data; name="file"; filename="{safe_filename}"\r\n'.encode("utf-8"))
    chunks.append(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
    chunks.append(file_data)
    chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return boundary, b"".join(chunks)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local AvelinLabs Customer Grounding live demo app.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host. Defaults to 127.0.0.1.")
    parser.add_argument("--port", type=int, default=8765, help="Bind port. Defaults to 8765.")
    parser.add_argument(
        "--allow-non-localhost",
        action="store_true",
        help="Allow binding outside localhost. Use only in a controlled local network demo.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.host not in LOCAL_HOSTS and not args.allow_non_localhost:
        raise SystemExit("Refusing non-localhost bind without --allow-non-localhost")
    os.chdir(APP_DIR)
    server = ThreadingHTTPServer((args.host, args.port), LocalDemoHandler)
    print(f"AvelinLabs Customer Grounding live demo app: http://{args.host}:{args.port}/")
    print("Runtime API key storage: process memory only; keys are never written by this app.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping live demo app.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
