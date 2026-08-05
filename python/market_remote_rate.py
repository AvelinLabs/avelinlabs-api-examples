from common import print_json, request_json


def main() -> None:
    result = request_json("GET", "/api/v1/market/remote-rate")
    print_json(result)


if __name__ == "__main__":
    main()
