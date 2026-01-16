import logging
import os
from collections.abc import AsyncGenerator, Mapping, Sequence
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Any, Final, cast
from frozendict import frozendict
from typing_extensions import override

import psycopg
import psycopg_pool
from async_lru import alru_cache
from psycopg import sql
from psycopg.rows import TupleRow

from src.sql.database import DatabaseClient, Params, Query
from src.sql.errors import NotConnectedError, SQLFailedMiserably

_LOGGER = logging.getLogger("SQL")


class PostgresDBClient(DatabaseClient):
    def __init__(self, conn_str: str | None = None, **kwargs: Any) -> None:
        """
        Initializes the database client.

        Will lazy-load the connection pool on first use.
        If you want to eagerly load, call :meth:`setup()` after initialization.

        Args:
            conn_str (str | None): The connection string to use.
                If None, will attempt to read from the environment variable
        """
        # Call super, even if it does nothing, for future compatibility
        super().__init__(conn_str)
        conn_str = (
            conn_str
            or os.getenv("SQL_CONNECTION_STRING")
            or self._create_conn_str_from_env(cast(str, kwargs.get("dbname")))
        )

        self._pool: Final = psycopg_pool.AsyncConnectionPool(
            conn_str, min_size=0, max_size=10, open=False, kwargs=kwargs
        )

        self._has_setup: bool = False

    @override
    async def setup(self, wait: bool = False, timeout: float = 30) -> None:
        """
        Sets up the database client, opening the connection pool.
        Normally not needed, as the pool will lazy-load on first use.
        """
        await self._pool.open(wait=wait, timeout=timeout)
        self._has_setup = True

    @override
    async def close(self):
        """
        Closes the connection to the database.
        """
        await self._pool.close()

    @property
    @asynccontextmanager
    async def _connection(self) -> AsyncGenerator[psycopg.AsyncConnection, None]:
        await self._pool.open()
        async with self._pool.connection() as conn:
            yield conn

    @property
    @override
    def connection(self) -> AbstractAsyncContextManager[psycopg.AsyncConnection]:
        return self._connection

    @property
    @asynccontextmanager
    async def _cursor(
        self,
    ) -> AsyncGenerator[tuple[psycopg.AsyncConnection, psycopg.AsyncCursor], None]:
        async with self.connection as conn:
            async with conn.cursor() as cursor:
                yield (conn, cursor)

    @property
    @override
    def cursor(
        self,
    ) -> AbstractAsyncContextManager[
        tuple[psycopg.AsyncConnection, psycopg.AsyncCursor]
    ]:
        return self._cursor

    def _create_conn_str_from_env(self, db_name: str | None = None) -> str:
        user = os.getenv("SQL_USER", "postgres")
        password = os.getenv("SQL_PASSWORD")
        database = db_name or os.getenv("SQL_DATABASE", "herifbot")
        host = os.getenv("SQL_HOST", "localhost")
        port = os.getenv("SQL_PORT", "5432")
        sslmode = os.getenv("SQL_SSLMODE", "require")
        channel_binding = os.getenv("SQL_CHANNELBINDING", "require")

        if not password:
            _LOGGER.error("No password found in environment variables")
            raise NotConnectedError("No password found in environment variables")

        return f"postgresql://{user}:{password}@{host}:{port}/{database}?sslmode={sslmode}&channel_binding={channel_binding}"

    @override
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
        async with self.cursor as (_, cursor):
            _ = await cursor.execute(query, params)

            return cursor.rowcount

    @override
    async def get(
        self, query: Query, params: Params[Any] | None = None
    ) -> list[TupleRow] | None:
        match params:
            case Mapping():
                new_params = cast(frozendict[str, Any], frozendict(params))
            case Sequence():
                new_params = tuple(params)
            case None:
                new_params = None
        match query:
            case sql.SQL() | sql.Composed():
                query_str = query.as_string()
            case str():  # Includes LiteralString, which is not a runtime type
                query_str = query
        return await self._get_cached(query_str, new_params)

    @alru_cache(maxsize=32, typed=True, ttl=0.5)
    async def _get_cached(
        self, query: Query, params: Params[Any] | None = None
    ) -> list[TupleRow] | None:
        return await self._get(query, params)

    # Cache the `get` method to avoid unnecessary database queries.
    # But do with TTL (Time To Live) to avoid caching forever.
    # Cache for 500 milliseconds
    # Should be more than enough for sudden bursts from func calls
    # The rest we don't need to cache for now anyways
    async def _get(
        self, query: Query, params: Params[Any] | None = None
    ) -> list[TupleRow] | None:
        """
        Executes a query and returns all results. Returns None if something goes wrong.

        Update and create a FrozenDict type to fix this.
        Args:
            query (Query): The query to execute.
            params (Sequence | None): The parameters to pass to the query.
                Defaults to None.

        Returns:
            list[TupleRow] | None: The result of the query.
        """

        async with self.cursor as (_, cursor):
            try:
                _ = await cursor.execute(query, params)
                _LOGGER.debug("Query ran successfully")
                return await cursor.fetchall()
            except psycopg.ProgrammingError:
                _LOGGER.debug("Query returned no results")
                return None
            except psycopg.Error as e:
                _LOGGER.error(
                    "Failed to run query: '%s', with values '%s'. Error: %s",
                    query,
                    params,
                    e,
                )
                raise SQLFailedMiserably("Query failed") from e

    def clear_cache(self) -> None:
        """
        Clears the query cache.
        """
        self._get_cached.cache_clear()


async def _main():
    # Only for testing purposes, so shut up pylint
    from dotenv import load_dotenv  # pylint: disable=import-outside-toplevel

    _ = load_dotenv()
    client = PostgresDBClient()
    print(await client.get("SELECT version()"))


if __name__ == "__main__":
    import asyncio

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(_main())
