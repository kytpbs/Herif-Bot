import psycopg2
from sql_wrapper import get, post

class AlreadyExistsError(Exception):
    pass

def get_all_responses():
    return get("SELECT * FROM responses;")

def add_response(response: tuple[str, str]):
    try:
        return post("INSERT INTO responses (question, answer) VALUES (%s, %s);", response)
    except psycopg2.errors.UniqueViolation as e: # pylint: disable=no-member # pylint is wrong, pylance knows this error exists
        raise AlreadyExistsError(f"Response for {response[0]} already exists") from e

def get_answer(question: str):
    responses = get_all_responses() or []
    for response in responses:
        if response[0] == question:
            return response[1]

    return get("SELECT answer FROM responses WHERE question = %s;", (question,))


if __name__ == "__main__":
    print(get_answer("sa"))
