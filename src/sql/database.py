import logging
import os
from collections.abc import AsyncGenerator, Mapping, Sequence
from contextlib import asynccontextmanager
from typing import Final, LiteralString, TypeAlias, TypeVar

import psycopg
import psycopg_pool
from async_lru import alru_cache
from psycopg import sql
from psycopg.rows import TupleRow

from src.sql.errors import NotConnectedError, SQLFailedMiserably

LOGGER = logging.getLogger("SQL")


T = TypeVar("T")

Params = Sequence[T] | Mapping[str, T]
Query: TypeAlias = LiteralString | sql.SQL | sql.Composed


class DatabaseClient:
    def __init__(self, conn_str: str | None = None):
        conn_str = (
            conn_str
            or os.getenv("SQL_CONNECTION_STRING")
            or self._create_conn_str_from_env()
        )

        self._pool: Final = psycopg_pool.AsyncConnectionPool(
            conn_str, min_size=0, max_size=10, open=False
        )
        pass

    async def close(self):
        """
        Closes the connection to the database.
        """
        await self._pool.close()

    @property
    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[psycopg.AsyncConnection, None]:
        async with self._pool.connection() as conn:
            yield conn

    @property
    @asynccontextmanager
    async def cursor(
        self,
    ) -> AsyncGenerator[tuple[psycopg.AsyncConnection, psycopg.AsyncCursor], None]:
        async with self._pool.connection() as conn:
            async with conn.cursor() as cursor:
                yield (conn, cursor)

    def _create_conn_str_from_env(self) -> str:
        user = os.getenv("SQL_USER", "postgres")
        password = os.getenv("SQL_PASSWORD")
        database = os.getenv("SQL_DATABASE", "herifbot")
        host = os.getenv("SQL_HOST", "localhost")
        port = os.getenv("SQL_PORT", "5432")
        sslmode = os.getenv("SQL_SSL_MODE", "require")
        channel_binding = os.getenv("SQL_CHANNEL_BINDING", "require")

        if not password:
            LOGGER.error("No password found in environment variables")
            raise NotConnectedError("No password found in environment variables")

        return f"postgresql://{user}:{password}@{host}:{port}/{database}?sslmode={sslmode}&channel_binding={channel_binding}"

    async def post(
        self, query: Query | sql.SQL, params: Params[T] | None = None
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

            cursor.pgresult
            return cursor.rowcount

    # Cache the `get` method to avoid unnecessary database queries.
    # But do with TTL (Time To Live) to avoid caching forever.
    # Cache for 100 milliseconds
    # Should be more than enough for sudden bursts from func calls
    # The rest we don't need to cache for now anyways
    @alru_cache(maxsize=32, typed=True, ttl=0.1)
    async def get(self, query: Query, params: Params[T]) -> list[TupleRow] | None:
        """
        Executes a query and returns the first result.

        This doesn't accept mapping types, due to caching issues.

        Update and create a FrozenDict type to fix this.
        Args:
            query (Query): The query to execute.
            params (Sequence | None): The parameters to pass to the query.
                Defaults to None.

        Returns:
            psycopg.AsyncResult: The result of the query.
        """
        LOGGER.debug("Executing query: '%s' with values: %s", query, params)

        async with self.cursor as (_, cursor):
            try:
                _ = await cursor.execute(query, params)
                LOGGER.debug("Query ran successfully")
                return await cursor.fetchall()
            except psycopg.ProgrammingError:
                LOGGER.debug("Query returned no results")
                return None
            except psycopg.Error as e:
                LOGGER.error(
                    "Failed to run query: '%s', with values '%s'. Error: %s",
                    query,
                    params,
                    e,
                )
                raise SQLFailedMiserably("Query failed") from e


async def _main():
    client = DatabaseClient()
    print(await client.get("SELECT version()"))


if __name__ == "__main__":
    import asyncio

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(_main())
