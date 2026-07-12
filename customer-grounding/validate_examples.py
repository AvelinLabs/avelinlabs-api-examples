from __future__ import annotations

import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parent
MAX_FILE_BYTES = 5 * 1024 * 1024


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
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Customer Grounding examples validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
