import json
from pathlib import Path

from common import print_json, request_json


INPUT_DIR = Path(__file__).resolve().parents[1] / "input-quality"


def main() -> None:
    for path in sorted(INPUT_DIR.glob("*.json")):
        print(f"\n# Input quality case: {path.name}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        result = request_json("POST", "/api/v1/job/analyze", payload=payload)
        print_json(result)


if __name__ == "__main__":
    main()
