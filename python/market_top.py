from urllib.parse import urlencode

from common import print_json, request_json


def main() -> None:
    query = urlencode({
        "type": "technology",
        "scope": "active",
        "country": "US",
        "limit": 5,
    })
    result = request_json("GET", f"/api/v1/market/top?{query}")
    print_json(result)


if __name__ == "__main__":
    main()
