import os

from common import print_json, request_json


def main() -> None:
    onet_code = os.environ.get("ONET_CODE", "15-1252.00")
    result = request_json("GET", f"/api/v1/occupation/{onet_code}")
    print_json(result)


if __name__ == "__main__":
    main()
