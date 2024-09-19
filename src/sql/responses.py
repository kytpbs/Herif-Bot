import psycopg2
from src.sql.sql_wrapper import LOGGER, NotConnectedError, get, post

class AlreadyExistsError(Exception):
    pass

NotConnectedToDBError = NotConnectedError

def get_all_responses():
    return get("SELECT * FROM responses;")

def add_response(response: tuple[str, str]):
    try:
        return post("INSERT INTO responses (question, answer) VALUES (%s, %s);", response)
    except psycopg2.errors.UniqueViolation as e: # pylint: disable=no-member # pylint is wrong, pylance knows this error exists
        raise AlreadyExistsError(f"Response for {response[0]} already exists") from e

def get_answers(question: str) -> list[str]:
    """Get all answers for a question, however many there are. returns an empty list if there are none.

    Args:
        question (str): the question to get the answers for

    Returns:
        list[str]: the answers to the question, or an empty list if there are none.
    """
    return get("SELECT answer FROM responses WHERE question = %s;", (question,)) or []

def get_answer(question: str) -> str | None:
    answers = get_answers(question)
    if not answers:
        return None
    return answers[0]



def sync_responses_dict_to_db(responses: dict[str, str]):
    rows = 0

    for response in responses.items():
        if get_answer(response[0]):
            LOGGER.debug("Response for %s already exists, skipping...", response[0])
            continue
        rows += add_response(response)

    return rows

if __name__ == "__main__":
    print(get_answer("sa"))
