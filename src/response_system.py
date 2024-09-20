import logging
from typing import Optional
from src.Helpers.helper_functions import DiskDict
from src.sql import responses

class CannotAddResponseError(Exception):
    pass

LOGGER = logging.getLogger("SQL")
custom_responses = DiskDict("responses.json")

def get_answer(question: str, guild_id: str | None = None) -> str | None:
    try:
        answer = responses.get_answer(question, guild_id)
        if answer:
            return answer
    except responses.NotConnectedToDBError as e:
        LOGGER.error("Failed to connect to the database: %s", e)

    # errored out or no answer found in the database, try the custom responses
    return custom_responses.get(question, None)

def set_answer(question: str, answer: str, guild_id: str | None = None) -> None:
    try:
        responses.add_response((question, answer), guild_id)
    except responses.AlreadyExistsError as e:
        LOGGER.error("Failed to add response: %s", e)
        raise CannotAddResponseError from e
    except responses.NotConnectedToDBError:
        LOGGER.warning("Not connected to the database, saving to disk instead")

    custom_responses[question] = answer


def get_data(guild_id: Optional[str] = None) -> list[tuple[str, str]]:
    try:
        results = responses.get_all_question_responses(guild_id)
        if results:
            return results
    except responses.NotConnectedToDBError:
        LOGGER.warning("Not connected to the database, saving to disk instead")

    return list(custom_responses.items())
