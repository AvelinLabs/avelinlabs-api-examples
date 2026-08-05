from common import load_payload, print_json, request_json


def main() -> None:
    payload = load_payload("occupation-candidates.json")
    result = request_json("POST", "/api/v1/occupation/candidates", payload=payload)
    print_json(result)


if __name__ == "__main__":
    main()
