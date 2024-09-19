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

def get_answer(question: str) -> str | None:
    return (get("SELECT answer FROM responses WHERE question = %s;", (question,)) or [None])[0]


if __name__ == "__main__":
    print(get_answer("sa"))
