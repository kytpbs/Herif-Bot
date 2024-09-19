import logging
import os
from typing import Optional

import psycopg2 # might want to use asyncpg instead, look into it later
from dotenv import load_dotenv

load_dotenv()

LOGGER = logging.getLogger("SQL")

database = os.getenv("SQL_DATABASE", "herifbot")
host = os.getenv("SQL_HOST", "localhost")
port = os.getenv("SQL_PORT", "5432")
user = os.getenv("SQL_USER", "postgres")
password = os.getenv("SQL_PASSWORD")

if all([database, host, port, user, password]):
    try:
        LOGGER.info("Connecting to the database...")
        conn = psycopg2.connect(
            database=database,
            host=host,
            port=port,
            user=user,
            password=password,
        )
    except psycopg2.OperationalError as e:
        LOGGER.error("Failed to connect to the database: %s", e)
        conn = None
else:
    LOGGER.error("Missing environment variables for SQL connection")
    conn = None


class NotConnectedError(Exception):
    pass

class SQLError(Exception):
    pass

class _Cursor:
    def __init__(self):
        if conn is None:
            raise NotConnectedError("No connection to the database")
        self.cursor = conn.cursor()

    def commit(self):
        if conn is None:
            raise NotConnectedError("No connection to the database")
        conn.commit()

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()


def post(query: str, values: Optional[tuple | list] = None) -> int:
    """
    Runs a query that changes the database.
    Returns the number of rows affected,
    if you need to get results use get() instead.

    Args:
        query (str): the query to run, with placeholders for values
        values (Optional[tuple  |  list], optional): the variables to be formatted into the query. IS SQL-Injection Safe. Defaults to None.

    Returns:
        int: the number of rows affected
    """
    with _Cursor() as cursor:
        cursor.execute(query, values)

        conn.commit()  # type: ignore  # with cursor already checks if conn is None

        return cursor.rowcount


def get(query: str, values: Optional[tuple | list] = None) -> Optional[list]:
    """Runs a query that fetches data from the database. and returns the result

    Args:
        query (str): the query to run, with placeholders for values
        values (Optional[tuple  |  list], optional): the variables to be formatted into the query. IS SQL-Injection Safe. Defaults to None.

    Returns:
        Optional[list]: returns the results of the query, or None if no results were returned like in an insert query
    """
    with _Cursor() as cursor:
        try:
            cursor.execute(query, values)
            results = cursor.fetchall()
        except psycopg2.ProgrammingError:
            LOGGER.error("No results found for query: %s with values %s.", query, values)
            results = None

    return results
