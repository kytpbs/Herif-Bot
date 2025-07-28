import os
from collections.abc import Mapping
from datetime import date
from typing import LiteralString

from src.data.birtdays import (
    BirthdayAlreadyExists,
    BirthdayDoesNotExist,
    Birthdays,
    BirthdayUnknownError,
    DBNotConnected,
)

from psycopg import sql

from src.sql.database import LOGGER, DatabaseClient


class BirthdaySQL(Birthdays):
    @classmethod
    async def create(cls, client: DatabaseClient) -> 'BirthdaySQL':
        instance = cls(client)
        await instance.start_up()
        return instance

    def __init__(self, client: DatabaseClient):
        self._db_client: DatabaseClient = client
        self._table_exists: bool = False
        self._table_name: str = os.getenv("BIRTHDAY_TABLE_NAME", "birthdays")

    @property
    def _client(self):
        if not self._table_exists:
            raise DBNotConnected("call start_up() because DB was not created)")
        return self._db_client

    async def start_up(self):
        await self._create_table_if_not_exists()

    async def _create_table_if_not_exists(self):
        LOGGER.debug("Creating Table if non-existent")
        LOGGER.debug("Setting DB time to UTC")

        query = sql.SQL("""
        SET TIME ZONE 'UTC';

        CREATE TABLE IF NOT EXISTS {0}(
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            guild_id BIGINT NOT NULL,
            birthday DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, guild_id)
        )

        """).format(
            sql.Identifier(self._table_name)
        )
        # Use db_client instead of _client to avoid getting an error
        _ = await self._db_client.post(query)
        self._table_exists = True
        LOGGER.info(f"Table {self._table_name} created or already exists")

    async def add_birthday(self, user_id: int, guild_id: int, birthday: str) -> None:
        query = sql.SQL("""
            INSERT INTO {0} (user_id, guild_id, birthday)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, guild_id) DO NOTHING
            """
        ).format(sql.Identifier(self._table_name))
        # Checking rows affected lets us not check for the birthday and save a query
        rows_affected = await self._client.post(
            query, (user_id, guild_id, birthday)
        )
        if rows_affected == 0:
            raise BirthdayAlreadyExists(f"Birthday for user {user_id} already exists")
        LOGGER.info(f"Added birthday for user {user_id} in guild {guild_id}")

    async def remove_birthday(self, user_id: int, guild_id: int) -> None:
        query = """
            DELETE FROM %s WHERE user_id = %s AND guild_id = %s
        """
        rows_affected = await self._client.post(query, (self._table_name, user_id, guild_id))
        if rows_affected < 1:
            raise BirthdayDoesNotExist()

    async def get_birthday(self, user_id: int, guild_id: int) -> date | None:
        query = """
            SELECT birthday FROM %s
            WHERE user_id = %s AND guild_id = %s
            """
        result = await self._client.get(query, (self._table_name, user_id, guild_id))
        if not result or not result[0] or not isinstance(result[0][0], date):
            return None
        return result[0][0]

    async def get_all_birthdays(self, guild_id: int) -> dict[int, date]:
        query = """
            SELECT user_id, birthday FROM %s
            WHERE guild_id = %s
        """
        result = await self._client.get(query, (self._table_name, guild_id))
        if not result:
            return {}
        try:
            return {row[0]: row[1] for row in result}
        except (ValueError, TypeError, IndexError) as e:
            raise BirthdayUnknownError("Somehow at least 2 rows did not exist") from e

    async def get_birthdays_on_date(
        self, guild_id: int, date: date
    ) -> Mapping[int, date]:
        query = """
            SELECT user_id, birthday FROM %s
            WHERE guild_id = %s
            AND EXTRACT(DAY FROM birthday)=EXTRACT(DAY FROM %s)
            AND EXTRACT(MONTH FROM birthday)=EXTRACT(MONTH FROM %s)
            """
        result = await self._client.get(query, (self._table_name, guild_id, date, date))
        if not result:
            return {}
        try:
            return {row[0]: row[1] for row in result}
        except (ValueError, TypeError, IndexError) as e:
            raise BirthdayUnknownError("Somehow at least 2 rows did not exist") from e

    async def get_birthdays_today(self, guild_id: int) -> Mapping[int, date]:
        query = """
            SELECT user_id, birthday FROM %s
            WHERE guild_id = %s
            AND EXTRACT(DAY FROM birthday)=EXTRACT(DAY FROM CURRENT_DATE)
            AND EXTRACT(MONTH FROM birthday)=EXTRACT(MONTH FROM CURRENT_DATE)
            """

        result = await self._client.get(query, (self._table_name, guild_id))
        if not result:
            return {}
        try:
            return {row[0]: row[1] for row in result}
        except (ValueError, TypeError, IndexError) as e:
            raise BirthdayUnknownError("Somehow at least 2 rows did not exist") from e

