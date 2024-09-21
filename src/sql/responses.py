from typing import Optional
from src.sql.sql_errors import NotConnectedError
from src.sql.sql_wrapper import LOGGER, get, post

class TooManyAnswersError(Exception):
    def __init__(self, message, current_answer: list[str]) -> None:
        super().__init__(message)
        self.current_answers = current_answer

class AlreadyExistsError(Exception):
    pass

NotConnectedToDBError = NotConnectedError

def get_all_question_responses(guild_id: Optional[str] = None) -> list[tuple[str, str]]:
    sql_query = "SELECT question, answer FROM responses"
    values = None
    if guild_id:
        sql_query += " WHERE guild_id = %s OR guild_id IS NULL"
        values = (guild_id,)
    result = get(sql_query, values)
    if not result:
        return []
    return result

def get_all_responses():
    return get("SELECT * FROM responses;")

def add_response(response: tuple[str, str], guild_id: Optional[str] = None) -> int:
    answers = get_answers(response[0], guild_id)

    if len(answers) > 2:
        raise TooManyAnswersError(f"Too many responses for {response[0]}", answers)

    if response[1] in answers:
        raise AlreadyExistsError(f"Answer {response[1]} already exists for {response[0]}")

    if guild_id:
        return post("INSERT INTO responses (question, answer, guild_id) VALUES (%s, %s, %s);", response + (guild_id,))
    return post("INSERT INTO responses (question, answer) VALUES (%s, %s);", response)

def get_answers(question: str, guild_id: Optional[str] = None) -> list[str]:
    """Get all answers for a question, however many there are. returns an empty list if there are none.

    Args:
        question (str): the question to get the answers for

    Returns:
        list[str]: the answers to the question, or an empty list if there are none.
    """
    values = [question]

    # global answers are answers that are not tied to a specific guild
    sql_query = "SELECT answer FROM global_answers WHERE question = %s"

    if guild_id:
        guild_query = "SELECT answer FROM responses WHERE question = %s AND guild_id = %s"
        sql_query += f" UNION {guild_query}"
        values += [question, guild_id]

    result_with_tuples = get(sql_query, values)
    if not result_with_tuples:
        return []
    # this returns a list of tuples each with a single element, so we need to extract the element
    return [result[0] for result in result_with_tuples]

def delete_answer(question: str, answer, guild_id: str) -> int:
    query = "DELETE FROM responses WHERE question = %s AND answer = %s AND guild_id = %s"
    return post(query, (question, answer, guild_id))


def get_answer(question: str, guild_id: Optional[str] = None) -> str | None:
    answers = get_answers(question, guild_id)
    if not answers:
        return None
    return answers[0]


def create_table_if_not_exists():
    return post(
        """
        CREATE TABLE IF NOT EXISTS responses (
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            guild_id BIGINT,
            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE OR REPLACE VIEW global_answers AS (
            SELECT question, answer FROM responses WHERE guild_id IS NULL
        );
        """
    )

def sync_responses_dict_to_db(responses: dict[str, str]):
    rows = 0

    for response in responses.items():
        # if response[0] in [db_response[0] for db_response in db_responses]:
        if get_answer(response[0]):
            LOGGER.debug("Response for %s already exists, skipping...", response[0])
            continue
        rows += add_response(response)

    return rows

try:
    create_table_if_not_exists() # at the start we might not have the table, so we create it
except NotConnectedToDBError:
    LOGGER.warning("No connection to the database")

if __name__ == "__main__":
    print(get_answer("sa"))
