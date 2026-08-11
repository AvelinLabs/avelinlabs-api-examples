import json
import os
import urllib.request
from pathlib import Path
from typing import Any
import zipfile

from jsonschema import Draft202012Validator
from jsonschema.validators import RefResolver


ROOT = Path(__file__).resolve().parent
MAX_FILE_BYTES = 5 * 1024 * 1024
OPENAPI_SPEC_URL = "https://raw.githubusercontent.com/AvelinLabs/avelin/main/backend/docs/openapi.json"


def _build_ref_resolver(openapi: dict[str, Any]) -> RefResolver:
    schemas = openapi.get("components", {}).get("schemas", {})
    resolver = RefResolver.from_schema(
        {"components": {"schemas": schemas}},
        store={f"#/components/schemas/{name}": schema for name, schema in schemas.items()},
    )
    return resolver


def _validation_errors(validator: Draft202012Validator, payload: Any, context: str, path: Path) -> list[str]:
    errors: list[str] = []
    for error in validator.iter_errors(payload):
        location = ".".join(str(item) for item in error.path)
        location = location or "<root>"
        errors.append(f"{path}: [{context}] {location}: {error.message}")
    return errors


def _load_openapi_spec() -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    repo_root = ROOT.parent
    candidate_paths = []
    env_path = Path(os.environ.get("OPENAPI_SPEC_PATH", "")).expanduser()
    if env_path:
        candidate_paths.append(env_path)
    candidate_paths.append(repo_root / "tmp_openapi.json")
    for path in candidate_paths:
        if not path:
            continue
        if not path.exists():
            continue
        try:
            return json.loads(path.read_text(encoding="utf-8-sig")), []
        except Exception as exc:
            errors.append(f"{path}: cannot load OpenAPI spec (JSON): {exc}")
            return None, errors
    try:
        with urllib.request.urlopen(OPENAPI_SPEC_URL, timeout=30) as response:
            return json.loads(response.read().decode("utf-8")), []
    except Exception as exc:
        errors.append(f"OpenAPI fetch from origin/main failed: {exc}")
    return None, errors


def validate_openapi_examples() -> list[str]:
    errors: list[str] = []
    openapi, openapi_errors = _load_openapi_spec()
    errors.extend(openapi_errors)
    if openapi is None:
        errors.append("OpenAPI validation skipped: unable to load AvelinLabs/avelin backend openapi.json from origin/main.")
        return errors

    request_schema = openapi.get("components", {}).get("schemas", {}).get("CustomerGroundingRoleReportRequest")
    response_schema = openapi.get("components", {}).get("schemas", {}).get("CustomerGroundingRoleReportResponse")
    if request_schema is None:
        errors.append("OpenAPI validation skipped: CustomerGroundingRoleReportRequest schema missing in openapi.json.")
        return errors
    if response_schema is None:
        errors.append("OpenAPI validation skipped: CustomerGroundingRoleReportResponse schema missing in openapi.json.")
        return errors

    resolver = _build_ref_resolver(openapi)
    request_validator = Draft202012Validator(request_schema, resolver=resolver)
    response_validator = Draft202012Validator(response_schema, resolver=resolver)

    request_paths = [
        ROOT / "requests" / "role-intelligence-report.json",
        ROOT / "requests" / "role-intelligence-report-passport-include.example.json",
    ]
    for path in request_paths:
        if not path.exists():
            errors.append(f"{path}: required request fixture missing")
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        errors.extend(_validation_errors(request_validator, payload, "CustomerGroundingRoleReportRequest", path))

    response_paths = [
        ROOT / "responses" / "role-intelligence-report-passport-level-1.example.json",
    ]
    for path in response_paths:
        if not path.exists():
            errors.append(f"{path}: required response fixture missing")
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        errors.extend(_validation_errors(response_validator, payload, "CustomerGroundingRoleReportResponse", path))

    return errors


def validate_json_files() -> list[str]:
    errors: list[str] = []
    for path in sorted(ROOT.rglob("*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{path}: invalid JSON: {exc}")
    return errors


def validate_python_files() -> list[str]:
    errors: list[str] = []
    for path in sorted((ROOT / "python").glob("*.py")) + [ROOT / "validate_examples.py"]:
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except Exception as exc:
            errors.append(f"{path}: Python syntax validation failed: {exc}")
    return errors


def validate_sample_files() -> list[str]:
    errors: list[str] = []
    sample_dir = ROOT / "sample-files"
    required = [
        "synthetic-role-criteria.txt",
        "synthetic-role-criteria.md",
        "synthetic-role-criteria.pdf",
        "synthetic-role-criteria.docx",
    ]
    for name in required:
        path = sample_dir / name
        if not path.exists():
            errors.append(f"{path}: missing sample file")
            continue
        if path.stat().st_size <= 0:
            errors.append(f"{path}: empty sample file")
        if path.stat().st_size > MAX_FILE_BYTES:
            errors.append(f"{path}: exceeds 5 MiB controlled-beta upload limit")
    for name in ("synthetic-role-criteria.txt", "synthetic-role-criteria.md"):
        path = sample_dir / name
        try:
            text = path.read_text(encoding="utf-8-sig")
            if "Synthetic" not in text and "synthetic" not in text:
                errors.append(f"{path}: expected synthetic marker")
        except Exception as exc:
            errors.append(f"{path}: UTF-8 validation failed: {exc}")
    pdf_path = sample_dir / "synthetic-role-criteria.pdf"
    if pdf_path.exists():
        data = pdf_path.read_bytes()
        if not data.startswith(b"%PDF-"):
            errors.append(f"{pdf_path}: missing PDF header")
        if b"%%EOF" not in data:
            errors.append(f"{pdf_path}: missing PDF EOF marker")
        try:
            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(str(pdf_path))
            if len(reader.pages) != 1:
                errors.append(f"{pdf_path}: expected one page")
            extracted = reader.pages[0].extract_text() or ""
            if "Synthetic" not in extracted:
                errors.append(f"{pdf_path}: expected extractable synthetic text")
        except ImportError:
            pass
        except Exception as exc:
            errors.append(f"{pdf_path}: PDF parser validation failed: {exc}")
    docx_path = sample_dir / "synthetic-role-criteria.docx"
    if docx_path.exists():
        try:
            with zipfile.ZipFile(docx_path) as archive:
                names = set(archive.namelist())
                if "[Content_Types].xml" not in names:
                    errors.append(f"{docx_path}: missing [Content_Types].xml")
                if "word/document.xml" not in names:
                    errors.append(f"{docx_path}: missing word/document.xml")
                lowered = {name.replace("\\", "/").lower() for name in names}
                if any(name.endswith("/vbaproject.bin") or name == "word/vbaproject.bin" for name in lowered):
                    errors.append(f"{docx_path}: macro member present")
                if any(name.startswith("word/embeddings/") for name in lowered):
                    errors.append(f"{docx_path}: embedded object member present")
        except zipfile.BadZipFile as exc:
            errors.append(f"{docx_path}: invalid DOCX ZIP: {exc}")
    return errors


def main() -> int:
    errors = validate_json_files() + validate_python_files() + validate_sample_files()
    openapi_errors = validate_openapi_examples()
    errors.extend(openapi_errors)
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Customer Grounding examples validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
