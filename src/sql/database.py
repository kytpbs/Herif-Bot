import functools
import logging
import os
from time import time
from typing import TypeVar
from collections.abc import Sequence, Mapping
import psycopg
from psycopg.rows import TupleRow

from src.sql.errors import NotConnectedError, SQLFailedMiserably

LOGGER = logging.getLogger("SQL")


T = TypeVar("T")

Params = Sequence[T] | Mapping[str, T]


class DatabaseClient:
    @classmethod
    async def create(cls):
        client = cls()
        try:
            await client.connect()
        except psycopg.OperationalError as e:
            raise NotConnectedError(e)
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
        if self.conn:
            await self.conn.close()

    @property
    def connection(self) -> psycopg.AsyncConnection:
        if not self.conn:
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

        self.conn = await psycopg.AsyncConnection.connect(
            user=os.getenv("SQL_USER", "postgres"),
            password=os.getenv("SQL_PASSWORD"),
            dbname=os.getenv("SQL_DATABASE", "herifbot"),
            host=os.getenv("SQL_HOST", "localhost"),
            port=os.getenv("SQL_PORT", "5432"),
            sslmode=os.getenv("SQL_SSL_MODE", "require"),
            channel_binding=os.getenv("SQL_CHANNEL_BINDING", "require"),
        )

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

    async def post(self, query: str, params: Params[T] = None):
        """
        Executes a query and returns the result.

        Args:
            query (str): The query to execute.
            params (tuple | list | dict | None): The parameters to pass to the query.
                Defaults to None.

        Returns:
            psycopg.AsyncResult: The result of the query.
        """
        async with self.connection.cursor() as cursor:
            if params:
                _ = await cursor.execute(query, params)
            else:
                _ = await cursor.execute(query)

            return await cursor.fetchall()

    # Cache the `get` method to avoid unnecessary database queries.
    # But do with TTL (Time To Live) to avoid caching forever.
    @functools.lru_cache(maxsize=32, typed=True)
    async def _get(
        self, query: str, params: Params[T] | None = None, ttl: int = None
    ) -> list[TupleRow] | None:
        del ttl  # This is passed so that the cache gets invalidated, not used.
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

    async def get(self, query: str, params: Params[T] | None = None):
        """
        Executes a query and returns the first result.

        Args:
            query (str): The query to execute.
            params (tuple | list | dict | None): The parameters to pass to the query.
                Defaults to None.

        Returns:
            psycopg.AsyncResult: The result of the query.
        """
        # Cache for 100 milliseconds with round to 1st decimal place
        # Should be more than enough for sudden bursts from func calls
        # The rest we don't need to cache for now anyways
        return await self._get(query, params, ttl=round(time(), 1))


async def _main():
    client = await DatabaseClient.create()
    # client = DatabaseClient()
    print(client.connection)


if __name__ == "__main__":
    import asyncio

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(_main())
