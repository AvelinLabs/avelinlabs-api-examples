from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
import zipfile

from jsonschema import Draft202012Validator
from jsonschema.validators import RefResolver


ROOT = Path(__file__).resolve().parent
MAX_FILE_BYTES = 5 * 1024 * 1024


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


def _load_json(path: Path) -> tuple[Any | None, str | None]:
    encodings = ("utf-8-sig", "utf-8", "utf-16", "utf-16le", "utf-16be")
    data = path.read_bytes()
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            text = data.decode(encoding)
        except Exception as exc:
            last_error = exc
            continue
        try:
            return json.loads(text), None
        except Exception as exc:
            return None, f"{path}: invalid JSON: {exc}"
    return None, f"{path}: unable to decode JSON (tried {', '.join(encodings)}): {last_error}"


def _semantic_id_set(payload: dict[str, Any]) -> set[str]:
    passport = payload.get("passport") or {}
    evidence = passport.get("evidence") if isinstance(passport, dict) else None
    refs = evidence.get("references") if isinstance(evidence, dict) else []
    return {
        str(ref.get("evidence_reference_id"))
        for ref in (refs or [])
        if isinstance(ref, dict) and ref.get("evidence_reference_id") is not None
    }


def _validate_passport_semantics(payload: dict[str, Any], *, path: Path) -> list[str]:
    errors: list[str] = []
    passport = payload.get("passport")
    if not isinstance(passport, dict):
        return errors

    decision = passport.get("decision") or {}
    if isinstance(decision, dict):
        trace = payload.get("trace") or {}
        if isinstance(trace, dict):
            passport_decision_id = decision.get("decision_id")
            trace_decision_id = trace.get("decision_id")
            if passport_decision_id and trace_decision_id and passport_decision_id != trace_decision_id:
                errors.append(
                    f"{path}: [passport] decision.decision_id ({passport_decision_id}) != trace.decision_id ({trace_decision_id})"
                )

        if decision.get("status") == "completed":
            governance = passport.get("governance") or {}
            human_review = governance.get("human_review") if isinstance(governance, dict) else None
            if not isinstance(human_review, dict):
                errors.append(f"{path}: [passport] completed decision requires governance.human_review object")
            else:
                if human_review.get("required") is not False or human_review.get("status") != "not_required":
                    errors.append(
                        f"{path}: [passport] completed decision requires human_review.required=false and human_review.status=not_required"
                    )
                if human_review.get("reasons") != []:
                    errors.append(f"{path}: [passport] completed decision requires human_review.reasons=[]")
    else:
        errors.append(f"{path}: [passport] decision must be object")

    versions = passport.get("versions") if isinstance(passport, dict) else None
    if isinstance(versions, dict):
        for key in ("decision_contract", "decision_policy", "taxonomy"):
            version_state = versions.get(key)
            if not isinstance(version_state, dict):
                continue
            if version_state.get("status") == "identified":
                if not version_state.get("value"):
                    errors.append(f"{path}: [passport] versions.{key}.value required when status=identified")
                if "reason" in version_state:
                    errors.append(f"{path}: [passport] versions.{key}.reason must be absent when status=identified")

    evidence = passport.get("evidence") if isinstance(passport, dict) else None
    if isinstance(evidence, dict):
        refs = evidence.get("references")
        if isinstance(refs, list):
            for idx, item in enumerate(refs):
                if not isinstance(item, dict):
                    continue
                source_version = item.get("source_version")
                if isinstance(source_version, dict) and source_version.get("status") == "identified":
                    if not source_version.get("value"):
                        errors.append(
                            f"{path}: [passport] evidence.references[{idx}].source_version.value required when status=identified"
                        )
                    if "reason" in source_version:
                        errors.append(
                            f"{path}: [passport] evidence.references[{idx}].source_version.reason must be absent when status=identified"
                        )

                relevance = item.get("relevance")
                if isinstance(relevance, dict) and relevance.get("status") == "assessed":
                    for field in ("score", "level", "method"):
                        if relevance.get(field) is None:
                            errors.append(
                                f"{path}: [passport] evidence.references[{idx}].relevance.{field} required when status=assessed"
                            )
                    if "reason" in relevance:
                        errors.append(
                            f"{path}: [passport] evidence.references[{idx}].relevance.reason must be absent when status=assessed"
                        )

        for idx, conflict in enumerate(evidence.get("conflicts") or []):
            if not isinstance(conflict, dict):
                continue
            conflict_ids = conflict.get("evidence_reference_ids")
            if isinstance(conflict_ids, list):
                known_refs = _semantic_id_set(payload)
                for conflict_id in conflict_ids:
                    if conflict_id not in known_refs:
                        errors.append(
                            f"{path}: [passport] evidence.conflicts[{idx}] references unknown evidence_reference_id={conflict_id}"
                        )

    assessment = passport.get("assessment") if isinstance(passport, dict) else None
    if isinstance(assessment, dict):
        confidence = assessment.get("confidence")
        if isinstance(confidence, dict) and confidence.get("status") == "assessed":
            for field in ("score", "level", "method"):
                if confidence.get(field) is None:
                    errors.append(f"{path}: [passport] assessment.confidence.{field} required when status=assessed")
            if "reason" in confidence:
                errors.append(f"{path}: [passport] assessment.confidence.reason must be absent when status=assessed")

    return errors


def _load_openapi_spec() -> tuple[dict[str, Any] | None, list[str], list[str]]:
    spec_path = os.environ.get("OPENAPI_SPEC_PATH", "").strip()
    errors: list[str] = []
    notes: list[str] = []
    if not spec_path:
        notes.append("OPENAPI_SPEC_PATH not set; OpenAPI contract validation not run.")
        return None, errors, notes

    path = Path(spec_path).expanduser()
    if not path.exists():
        errors.append(f"OPENAPI_SPEC_PATH provided but file not found: {path}")
        return None, errors, notes

    payload, parse_error = _load_json(path)
    if parse_error is not None:
        errors.append(parse_error)
        return None, errors, notes

    return payload, [], notes


def validate_openapi_examples() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []
    openapi, openapi_errors, openapi_notes = _load_openapi_spec()
    errors.extend(openapi_errors)
    notes.extend(openapi_notes)
    if openapi is None:
        return errors, notes

    request_schema = openapi.get("components", {}).get("schemas", {}).get("CustomerGroundingRoleReportRequest")
    response_schema = openapi.get("components", {}).get("schemas", {}).get("CustomerGroundingRoleReportResponse")
    if request_schema is None:
        errors.append("CustomerGroundingRoleReportRequest schema missing in openapi.json.")
        return errors, notes
    if response_schema is None:
        errors.append("CustomerGroundingRoleReportResponse schema missing in openapi.json.")
        return errors, notes

    resolver = _build_ref_resolver(openapi)
    request_validator = Draft202012Validator(request_schema, resolver=resolver)
    response_validator = Draft202012Validator(response_schema, resolver=resolver) if response_schema else None

    request_paths = [
        ROOT / "requests" / "role-intelligence-report.json",
        ROOT / "requests" / "role-intelligence-report-passport-include.example.json",
    ]
    for path in request_paths:
        if not path.exists():
            errors.append(f"{path}: required request fixture missing")
            continue
        payload, parse_error = _load_json(path)
        if parse_error is not None:
            errors.append(parse_error)
            continue
        errors.extend(_validation_errors(request_validator, payload, "CustomerGroundingRoleReportRequest", path))

    response_paths = [
        ROOT / "responses" / "role-intelligence-report-passport-level-1.example.json",
    ]
    for path in response_paths:
        if not path.exists():
            errors.append(f"{path}: required response fixture missing")
            continue
        payload, parse_error = _load_json(path)
        if parse_error is not None:
            errors.append(parse_error)
            continue
        if response_validator is not None:
            errors.extend(_validation_errors(response_validator, payload, "CustomerGroundingRoleReportResponse", path))
        errors.extend(_validate_passport_semantics(payload, path=path))

    return errors, notes


def validate_customer_grounding_passport_semantics() -> list[str]:
    errors: list[str] = []
    path = ROOT / "responses" / "role-intelligence-report-passport-level-1.example.json"
    if not path.exists():
        return [f"{path}: required response fixture missing"]

    payload, parse_error = _load_json(path)
    if parse_error is not None:
        errors.append(parse_error)
        return errors

    errors.extend(_validate_passport_semantics(payload, path=path))
    return errors


def validate_json_files() -> list[str]:
    errors: list[str] = []
    for path in sorted(ROOT.rglob("*.json")):
        _, parse_error = _load_json(path)
        if parse_error is not None:
            errors.append(parse_error)
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
    errors.extend(validate_customer_grounding_passport_semantics())
    openapi_errors, openapi_notes = validate_openapi_examples()
    errors.extend(openapi_errors)
    for note in openapi_notes:
        print(note)
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Customer Grounding examples validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
