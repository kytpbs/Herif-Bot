import json


def json_read(name: str) -> dict:
    with open(name) as json_file:
        print(f"Reading {name}")
        data = json.load(json_file)
    return data
