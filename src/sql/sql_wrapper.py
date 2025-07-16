import functools
import logging
import os
import time
from typing import Optional

import psycopg2  # might want to use asyncpg instead, look into it later
from dotenv import load_dotenv
from src.sql.sql_errors import NotConnectedError, SQLFailedMiserably

load_dotenv()

LOGGER = logging.getLogger("SQL")
_CACHE_INVALIDATION_TTL_SECONDS = 0.25  # 250 milliseconds


database = os.getenv("SQL_DATABASE", "herifbot")
host = os.getenv("SQL_HOST", "localhost")
port = os.getenv("SQL_PORT", "5432")
user = os.getenv("SQL_USER", "postgres")
password = os.getenv("SQL_PASSWORD")


def connect_to_db():
    if not all([database, host, port, user, password]):
        LOGGER.error("Missing environment variables for SQL connection")
        LOGGER.error(
            "Database: %s, Host: %s, Port: %s, User: %s", database, host, port, user
        )
        LOGGER.error("Please check your .env file or environment variables")
        return None

    try:
        LOGGER.info(
            "Connecting to the database... %s at %s:%s with user: %s",
            database,
            host,
            port,
            user,
        )
        return psycopg2.connect(
            database=database,
            host=host,
            port=port,
            user=user,
            password=password,
        )
    except psycopg2.OperationalError as e2:
        LOGGER.error("Failed to connect to the database: %s", e2)
        return None


conn = connect_to_db()


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

    Raises:
        NotConnectedError: if there is no connection to the database
        SQLFailedMiserably: if the query fails
    """
    with _Cursor() as cursor:
        cursor.execute(query, values)

        conn.commit()  # type: ignore  # with cursor already checks if conn is None

        return cursor.rowcount


# make it cached for a 250ms, since it may be called multiple times in a short period
# ttl_hash will be passed by the actual `get_birthday` function, which will be make the cache "expire"
@functools.lru_cache(maxsize=128, typed=True)
def _get(
    query: str, values: tuple | list | None = None, ttl: int = 0
) -> list[tuple] | None:
    del ttl  # the argument is actually used to invalidate the lru_cache, but we won't need it in the actual function

    with _Cursor() as cursor:
        try:
            LOGGER.debug("Running query: %s with values: %s", query, values)
            cursor.execute(query, values)
            results = cursor.fetchall()
            LOGGER.debug("Query ran successfully")
        except psycopg2.ProgrammingError:
            LOGGER.error(
                "No results found for query: %s with values %s.", query, values
            )
            results = None
        except psycopg2.Error as e:
            LOGGER.error(
                "Failed to run query: %s with values %s. Error: %s", query, values, e
            )
            raise SQLFailedMiserably("Failed to run query") from e

    return results


def get(
    query: str, values: tuple | list | None = None, ttl: int = 0
) -> list[tuple] | None:
    """Runs a query that fetches data from the database. and returns the result

    Will cache the results for 250 milliseconds to avoid hitting the database too often.
    If you need to invalidate the cache, pass a different `ttl` value to the function.


    Args:
        query (str): the query to run, with placeholders for values
        values (Optional[tuple  |  list], optional): the variables to be formatted into the query. IS SQL-Injection Safe. Defaults to None.
        ttl (int, optional): the time to live for the cache in seconds. Defaults to 0, which means cached for 250 milliseconds.

    Returns:
        Optional[list]: returns the results of the query, or None if no results were returned like in an insert query

    Raises:
        NotConnectedError: if there is no connection to the database
        SQLFailedMiserably: if the query fails
    """

    if isinstance(
        values, list
    ):  # convert list to tuple for psycopg2 compatibility and for lru_cache
        values = tuple(values)

    return _get(
        query,
        values,
        ttl=ttl or round(time.time() / _CACHE_INVALIDATION_TTL_SECONDS, 1),
    )
