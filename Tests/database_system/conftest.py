
from typing import AsyncGenerator
import psycopg_pool
import pytest

from src.sql.postgres import PostgresDBClient


@pytest.fixture(scope="session")
async def client() -> AsyncGenerator[PostgresDBClient, None]:
    try:
        db_client = PostgresDBClient(dbname="herif_bot_test")
        await db_client.setup(wait=True, timeout=5)
        async with db_client.cursor as (_, cursor):
            await cursor.execute("SELECT 1;")
    except psycopg_pool.PoolTimeout:
        # Try recovering by creating the database, then connecting again
        temp_client = PostgresDBClient(dbname="postgres")
        async with temp_client.connection as conn:
            await conn.set_autocommit(True)
            await conn.execute("CREATE DATABASE herif_bot_test")
        await temp_client.close()

        db_client = PostgresDBClient(dbname="herif_bot_test")
        await db_client.setup()


    yield db_client
    await db_client.close()
