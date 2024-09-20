from typing import Optional
import psycopg2
from src.sql.sql_errors import NotConnectedError
from src.sql.sql_wrapper import LOGGER, get, post

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
    try:
        return post("INSERT INTO responses (question, answer, guild_id) VALUES (%s, %s, %s);", response + (guild_id,))
    except psycopg2.errors.UniqueViolation as e: # pylint: disable=no-member # pylint is wrong, pylance knows this error exists
        raise AlreadyExistsError(f"Response for {response[0]} already exists") from e

def get_answers(question: str, guild_id: Optional[str] = None) -> list[str]:
    """Get all answers for a question, however many there are. returns an empty list if there are none.

    Args:
        question (str): the question to get the answers for

    Returns:
        list[str]: the answers to the question, or an empty list if there are none.
    """
    values = [question]
    sql_query = "SELECT answer FROM responses WHERE question = %s"
    if guild_id:
        sql_query += " AND guild_id = %s OR guild_id IS NULL"
        values.append(guild_id)
    else:
        sql_query += " AND guild_id IS NULL"
    result_with_tuples = get(sql_query, values)
    if not result_with_tuples:
        return []
    # this returns a list of tuples each with a single element, so we need to extract the element
    return [result[0] for result in result_with_tuples]

def get_answer(question: str, guild_id: Optional[str] = None) -> str | None:
    answers = get_answers(question, guild_id)
    if not answers:
        return None
    return answers[0]


def create_table_if_not_exists():
    return post(
        """
        CREATE TABLE IF NOT EXISTS responses (
            question TEXT,
            answer TEXT,
            guild_id BIGINT,
            timestamp timestamp default current_timestamp
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


create_table_if_not_exists() # at the start we might not have the table, so we create it

if __name__ == "__main__":
    print(get_answer("sa"))
