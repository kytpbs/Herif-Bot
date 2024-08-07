import json
import logging
import os

from Constants import JSON_FOLDER
FILE_EXTENSION = ".json"

def json_read(name: str) -> dict:
    """
    Reads a json file with the given name and returns the data.
    Adds .json to the end of the name if it is not there.
    Adds it to 'jsons' folder if it is not there.
    If the file does not exist, it will be created.
    """
    if not name.startswith(JSON_FOLDER):
        name = JSON_FOLDER + name
    if not name.endswith(FILE_EXTENSION):
        name += FILE_EXTENSION
    if not os.path.exists(name):
        write_json(name, {})
        return {}
    with open(name, encoding="utf-8") as json_file:
        logging.debug(f"Reading {name}")
        data = json.load(json_file)
    return data


def write_json(name: str, data: dict[str, str]) -> None:
    """
    Writes a json file with the given name and data
    Adds .json to the end of the name if it is not there.
    Adds it to 'jsons' folder if it is not there.
    """
    if not name.startswith(JSON_FOLDER):
        name = JSON_FOLDER + name
    if not name.endswith(FILE_EXTENSION):
        name += FILE_EXTENSION
    with open(name, 'w+', encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        f.close()
    logging.debug(f"Writing to {name}")
