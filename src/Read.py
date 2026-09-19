import contextlib
from dataclasses import asdict, is_dataclass
from datetime import date
import json
import logging
import os
from typing import Any, overload

from Constants import JSON_FOLDER

FILE_EXTENSION = ".json"


class DateEncoder(json.JSONEncoder):
    def default(self, o: object):
        """Serialize dates as ISO strings and dataclass instances as dictionaries."""
        if isinstance(o, date):
            return o.isoformat()  # Convert to string like "2025-07-29"
        if is_dataclass(o) and not isinstance(o, type):
            return asdict(o)
        return super().default(o)


def _date_hook(dct: dict[str, Any]):
    """Convert ISO-formatted date values in a decoded JSON object to dates."""
    for key, value in dct.items():
        if isinstance(value, str):
            with contextlib.suppress(ValueError):
                dct[key] = date.fromisoformat(value)
    return dct


@overload
def json_read(name: str) -> dict[Any, Any]: ...


@overload
def json_read(
    name: str, create_if_not_exists: bool = True
) -> dict[Any, Any] | None: ...


def json_read(name: str, create_if_not_exists: bool = True) -> dict[Any, Any] | None:
    """Read a JSON object from the configured JSON directory.

    The ``.json`` suffix and JSON directory prefix are added when absent. ISO
    date strings are decoded as dates. If the file is missing, an empty file is
    created and returned unless ``create_if_not_exists`` is false, in which case
    ``None`` is returned.
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
        data = json.load(json_file, object_hook=_date_hook)
    return data


def write_json(name: str, data: dict[Any, Any]) -> None:
    """Write a mapping as indented JSON in the configured JSON directory.

    The ``.json`` suffix and JSON directory prefix are added when absent. Date
    values and dataclass instances are converted by :class:`DateEncoder`.
    """
    if not name.endswith(FILE_EXTENSION):
        name += FILE_EXTENSION
    if not name.startswith(JSON_FOLDER):
        name = os.path.join(JSON_FOLDER, name)
    os.makedirs(JSON_FOLDER, exist_ok=True)
    with open(name, "w+", encoding="utf-8") as f:
        json.dump(data, f, indent=4, cls=DateEncoder)
        f.close()
    logging.debug(f"Writing to {name}")
