from abc import ABC, abstractmethod
import logging
import os
from collections.abc import Mapping, Sequence
from contextlib import AbstractAsyncContextManager
from typing import Any, LiteralString, TypeAlias, TypeVar

import psycopg
from psycopg import sql
from psycopg.rows import TupleRow
from dotenv import load_dotenv

from src.sql.errors import NotConnectedError

LOGGER = logging.getLogger("SQL")
_ = load_dotenv()


T = TypeVar("T")

Params: TypeAlias = Sequence[T] | Mapping[str, T]
Query: TypeAlias = LiteralString | sql.SQL | sql.Composed


class DatabaseClient(ABC):
    @abstractmethod
    def __init__(self, conn_str: str | None = None) -> None:
        """
        Initializes the database client.

        Will lazy-load the connection pool on first use.
        If you want to eagerly load, call :meth:`setup()` after initialization.

        Args:
            conn_str (str | None): The connection string to use.
                If None, will attempt to read from the environment variable
        """

    @abstractmethod
    async def setup(self) -> None:
        """
        Sets up the database client, opening the connection pool.
        Normally not needed, as the pool will lazy-load on first use.
        """

    @abstractmethod
    async def close(self) -> None:
        """
        Closes the connection to the database.
        """

    @property
    @abstractmethod
    async def connection(
        self,
    ) -> AbstractAsyncContextManager[psycopg.AsyncConnection]: ...

    @property
    @abstractmethod
    async def cursor(
        self,
    ) -> AbstractAsyncContextManager[
        tuple[psycopg.AsyncConnection, psycopg.AsyncCursor]
    ]: ...

    def _create_conn_str_from_env(self) -> str:
        user = os.getenv("SQL_USER", "postgres")
        password = os.getenv("SQL_PASSWORD")
        database = os.getenv("SQL_DATABASE", "herifbot")
        host = os.getenv("SQL_HOST", "localhost")
        port = os.getenv("SQL_PORT", "5432")
        sslmode = os.getenv("SQL_SSLMODE", "require")
        channel_binding = os.getenv("SQL_CHANNELBINDING", "require")

        if not password:
            LOGGER.error("No password found in environment variables")
            raise NotConnectedError("No password found in environment variables")

        return f"postgresql://{user}:{password}@{host}:{port}/{database}?sslmode={sslmode}&channel_binding={channel_binding}"

    @abstractmethod
    async def post(
        self, query: Query | sql.SQL, params: Params[Any] | None = None
    ) -> int:
        """
        Executes a query and returns the number of rows affected by the query.
        This should be used for INSERT, UPDATE, and DELETE queries.

        If you want to get the result of a query, use :meth:`get()`.

        Args:
            query (str): The query to execute.
            params (tuple | list | dict | None): The parameters to pass to the query.
                Defaults to None.

        Returns:
            int: The number of rows affected by the query.
        """

    # The rest we don't need to cache for now anyways
    @abstractmethod
    async def get(
        self, query: Query, params: Params[Any] | None = None
    ) -> list[TupleRow] | None:
        """
        Executes a query and returns the first result.
        has a limiter cache to prevent repeated queries,
        if you need to bypass the cache, update the query slightly,
        a new API will be made with more options later.

        This doesn't accept mapping types, due to caching issues.

        Update and create a FrozenDict type to fix this.
        Args:
            query (Query): The query to execute.
            params (Sequence | None): The parameters to pass to the query.
                Defaults to None.

        Returns:
            psycopg.AsyncResult: The result of the query.
        """
