import json
import logging
import os
from typing import overload

from Constants import JSON_FOLDER
FILE_EXTENSION = ".json"


@overload
def json_read(name: str) -> dict: 
    ...

@overload
def json_read(name: str, create_if_not_exists: bool = True) -> dict | None: 
    ...

def json_read(name: str, create_if_not_exists: bool = True) -> dict | None:
    """
    Reads a json file with the given name and returns the data.
    Adds .json to the end of the name if it is not there.
    Adds it to 'jsons' folder if it is not there.
    If the file does not exist, it will be created.
    """
    if not name.endswith(FILE_EXTENSION):
        name += FILE_EXTENSION
    if not name.startswith(JSON_FOLDER):
        name = os.path.join(JSON_FOLDER, name)
    if not os.path.exists(name):
        if not create_if_not_exists:
            return None
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
    if not name.endswith(FILE_EXTENSION):
        name += FILE_EXTENSION
    if not name.startswith(JSON_FOLDER):
        name = os.path.join(JSON_FOLDER, name)
    os.makedirs(JSON_FOLDER, exist_ok=True)
    with open(name, 'w+', encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        f.close()
    logging.debug(f"Writing to {name}")
