import logging
from typing import Optional
from src.Helpers.helper_functions import DiskDict
from src.sql import responses

_NOT_CONNECTED_ERROR_MESSAGE = "Not connected to the database, saving to disk instead"
class CannotAddResponseError(Exception):
    pass

LOGGER = logging.getLogger("response_system")
custom_responses = DiskDict("responses.json")


def get_answers(question: str, guild_id: str | None = None) -> list[str]:
    try:
        answers = responses.get_answers(question, guild_id)
        if answers:
            return answers
    except responses.NotConnectedToDBError:
        LOGGER.warning(_NOT_CONNECTED_ERROR_MESSAGE)

    return [custom_responses.get(question, None)]

def get_answer(question: str, guild_id: str | None = None) -> str | None:
    return get_answers(question, guild_id)[0]

def set_answer(question: str, answer: str, guild_id: str | None = None) -> None:
    try:
        responses.add_response((question, answer), guild_id)
    except responses.AlreadyExistsError as e:
        LOGGER.error("Failed to add response: %s", e)
        raise CannotAddResponseError from e
    except responses.NotConnectedToDBError:
        LOGGER.warning(_NOT_CONNECTED_ERROR_MESSAGE)

    custom_responses[question] = answer


def get_data(guild_id: Optional[str] = None) -> list[tuple[str, str]]:
    try:
        results = responses.get_all_question_responses(guild_id)
        if results:
            return results
    except responses.NotConnectedToDBError:
        LOGGER.warning(_NOT_CONNECTED_ERROR_MESSAGE)

    return list(custom_responses.items())
