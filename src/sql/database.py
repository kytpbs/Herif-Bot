import logging
import os
from collections.abc import Mapping, Sequence
from typing import LiteralString, TypeAlias, TypeVar

import psycopg
from async_lru import alru_cache
from psycopg import sql
from psycopg.rows import TupleRow

from src.sql.errors import NotConnectedError, SQLFailedMiserably

LOGGER = logging.getLogger("SQL")


T = TypeVar("T")

Params = Sequence[T] | Mapping[str, T]
Query: TypeAlias = LiteralString | sql.SQL | sql.Composed


class DatabaseClient:
    @classmethod
    async def create(cls):
        client = cls()
        try:
            await client.connect()
        except psycopg.OperationalError as e:
            raise NotConnectedError(e) from e
        return client

    def __init__(self):
        """
        Initializes the database client.

        Auto connects to the database.
        Raises an error if connection fails.

        Raises:
            DatabaseConnectionError: If the connection fails.
        """
        self.conn: psycopg.AsyncConnection | None = None

    async def close(self):
        """
        Closes the connection to the database.
        """
        if self.conn is not None and not self.conn.closed:
            await self.conn.close()

    @property
    def connection(self) -> psycopg.AsyncConnection:
        if not self.conn or self.conn.closed:
            # This should never happen unless __init__ was directly called
            # and then connect() was never called.
            raise NotConnectedError("Database not connected, call connect()")
        return self.conn

    async def connect(self):
        """
        Connects to the database.
        Raises an error if connection fails.

        Raises:
            DatabaseConnectionError: If the connection fails.
        """
        if self.conn and not self.conn.closed:
            return

        if self.conn:
            await self.conn.close()

        await self._connect()

    async def _connect(self):
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

        self.conn = await psycopg.AsyncConnection.connect(
            user=user,
            password=password,
            dbname=database,
            host=host,
            port=port,
            sslmode=sslmode,
            channel_binding=channel_binding,
        )

    async def post(self, query: Query | sql.SQL, params: Params[T] | None = None) -> int:
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
        async with self.connection.cursor() as cursor:
            _ = await cursor.execute(query, params)

            cursor.pgresult
            return cursor.rowcount

    # Cache the `get` method to avoid unnecessary database queries.
    # But do with TTL (Time To Live) to avoid caching forever.
    # Cache for 100 milliseconds
    # Should be more than enough for sudden bursts from func calls
    # The rest we don't need to cache for now anyways
    @alru_cache(maxsize=32, typed=True, ttl=0.1)
    async def get(
        self, query: Query, params: Params[T]
    ) -> list[TupleRow] | None:
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

        async with self.connection.cursor() as cursor:
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

    def __del__(self):
        """
        Cleanup method called when the object is garbage collected.
        Warns if the connection is still open.
        """
        if self.conn and not self.conn.closed:
            LOGGER.warning(
                "DatabaseClient was deleted with an open connection. "
                "Please call close() or use as an async context manager."
            )


async def _main():
    client = await DatabaseClient.create()
    # client = DatabaseClient()
    print(client.connection)


if __name__ == "__main__":
    import asyncio

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(_main())
