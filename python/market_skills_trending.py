from urllib.parse import urlencode

from common import print_json, request_json


def main() -> None:
    query = urlencode({"limit": 20})
    result = request_json("GET", f"/api/v1/market/skills/trending?{query}")
    print_json(result)


if __name__ == "__main__":
    main()
