

import logging
from datetime import date
from typing import Sequence

from src.Helpers.helper_functions import DiskDict
from src.sql import birthdays
from src.sql.sql_errors import AlreadyExistsError, NotConnectedError

_NOT_CONNECTED_ERROR_MESSAGE = "Not connected to the database, using local dict instead."

class CannotAddBirthdayError(Exception):
    pass

LOGGER = logging.getLogger("birthday_system")
birthdays_dict: dict[str, str] = DiskDict("birthdays.json")

def _to_str(date_: date) -> str:
    return date_.strftime("%Y-%m-%d")
def _from_str(date_: str) -> date:
    return date(*map(int, date_.split("-")))

def get_birthday(user_id: str, guild_id: str | None = None) -> date | None:
    try:
        birthday = birthdays.get_birthday(user_id, guild_id)
        if birthday is not None:
            return birthday
    except NotConnectedError:
        LOGGER.warning(_NOT_CONNECTED_ERROR_MESSAGE)

    birthday = birthdays_dict.get(user_id, None)
    if not birthday:
        return None
    return _from_str(birthday)

def find_user_and_guild_from_birthday(birthday: date) -> Sequence[tuple[int, int | None]]:
    """Find all users who have a birthday on the given date

    Args:
        birthday (date): the birthday to find users for

    Returns:
        Sequence[tuple[int, int | None]: a list of tuples with the user_id and the guild_id
        If not connected to the database, returns a list of user_ids with a guild_id of None
    """
    try:
        return birthdays.find_users(birthday)
    except NotConnectedError:
        LOGGER.warning(_NOT_CONNECTED_ERROR_MESSAGE)

    user_ids = [user_id for user_id, user_birthday in birthdays_dict.items() if user_birthday == _to_str(birthday)]
    return [(int(user_id), 0) for user_id in user_ids]

def find_users_birthday(birthday: date, guild_id: str | None = None) -> list[int]:
    try:
        return birthdays.get_users_birthday(birthday, guild_id)
    except NotConnectedError:
        LOGGER.warning(_NOT_CONNECTED_ERROR_MESSAGE)

    user_ids = [user_id for user_id, user_birthday in birthdays_dict.items() if user_birthday == _to_str(birthday)]
    return [int(user_id) for user_id in user_ids]

def add_birthday(user_id: str, birthday: date, guild_id: str) -> bool:
    try:
        rows_affected = birthdays.add_birthday(user_id, birthday, guild_id)
        return rows_affected > 0
    except NotConnectedError:
        LOGGER.warning(_NOT_CONNECTED_ERROR_MESSAGE)

    if user_id in birthdays_dict:
        raise AlreadyExistsError(f"Birthday for user {user_id}, already exists in custom birthdays dict", birthdays_dict[user_id])

    birthdays_dict[user_id] = _to_str(birthday)
    return True

def get_all_birthdays(guild_id: str | int) -> list[tuple[int, date]]:
    try:
        return birthdays.get_all_birthdays(guild_id)
    except NotConnectedError:
        LOGGER.warning(_NOT_CONNECTED_ERROR_MESSAGE)

    birthday_dates = {int(user_id): _from_str(birthday) for user_id, birthday in birthdays_dict.items()}
    return list(birthday_dates.items())

def remove_birthday(user_id: str, guild_id: str) -> bool:
    try:
        counts_affected = birthdays.delete_birthday(user_id, guild_id)
        return counts_affected > 0
    except NotConnectedError:
        LOGGER.warning(_NOT_CONNECTED_ERROR_MESSAGE)

    if user_id not in birthdays_dict:
        return False
    del birthdays_dict[user_id]
    return True
