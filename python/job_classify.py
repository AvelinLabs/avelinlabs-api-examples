from common import load_payload, print_json, request_json


def main() -> None:
    payload = load_payload("job-classify.json")
    result = request_json("POST", "/api/v1/job/classify", payload=payload)
    print_json(result)


if __name__ == "__main__":
    main()
