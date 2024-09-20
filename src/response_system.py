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
        if answers is not None:
            return answers
    except responses.NotConnectedToDBError:
        LOGGER.warning(_NOT_CONNECTED_ERROR_MESSAGE)

    return [custom_responses.get(question, None)]

def get_answer(question: str, guild_id: str | None = None) -> str | None:
    return get_answers(question, guild_id)[0]

def add_answer(question: str, answer: str, guild_id: str | None = None) -> bool:
    try:
        rows_affected = responses.add_response((question, answer), guild_id)
        return rows_affected > 0
    except responses.NotConnectedToDBError:
        LOGGER.warning(_NOT_CONNECTED_ERROR_MESSAGE)

    if question in custom_responses:
        raise responses.TooManyAnswersError(f"Too many responses for {question}", custom_responses[question])

    custom_responses[question] = answer
    return True

def remove_answer(question: str, answer: str, guild_id: str) -> bool:
    """Remove a response from the database and the custom responses.
    guild_id is required to remove the response from the database, due to security reasons.
    if you wish to delete non-guild specific responses, use the underlying database directly.

    Args:
        question (str): the question to remove the answer from
        answer (str): the answer to the question to remove
        guild_id (str): the guild id to remove the answer from
        Must be provided for security reasons.
    """
    try:
        counts_affected = responses.delete_answer(question, answer, guild_id)
        return counts_affected > 0
    except responses.NotConnectedToDBError:
        LOGGER.warning(_NOT_CONNECTED_ERROR_MESSAGE)

    if question not in custom_responses:
        return False
    del custom_responses[question]
    return True

def get_data(guild_id: Optional[str] = None) -> list[tuple[str, str]]:
    try:
        results = responses.get_all_question_responses(guild_id)
        if results:
            return results
    except responses.NotConnectedToDBError:
        LOGGER.warning(_NOT_CONNECTED_ERROR_MESSAGE)

    return list(custom_responses.items())
