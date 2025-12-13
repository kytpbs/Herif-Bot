import os
from collections.abc import Mapping
from datetime import date

from psycopg import sql
from typing_extensions import override

from src.data.birtdays import (
    BirthdayAlreadyExists,
    BirthdayDoesNotExist,
    BirthdayProvider,
    BirthdayUnknownError,
    DBNotConnected,
    GuildID,
    UserID,
)
from src.sql.database import LOGGER, DatabaseClient

_LOGGER = LOGGER.getChild("BirthdaySQL")


class BirthdaySQL(BirthdayProvider):
    @classmethod
    async def create(cls, client: DatabaseClient) -> "BirthdaySQL":
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
        _LOGGER.debug("Creating Table if non-existent")
        _LOGGER.debug("Setting DB time to UTC")

        query = sql.SQL("""
        SET TIME ZONE 'UTC';

        CREATE TABLE IF NOT EXISTS {table_name}(
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            guild_id BIGINT NOT NULL,
            birthday DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, guild_id)
        );

        CREATE INDEX IF NOT EXISTS {idx_get} on {table_name}(guild_id, user_id);
        CREATE INDEX IF NOT EXISTS {idx_users} on {table_name}(user_id);

        CREATE INDEX IF NOT EXISTS {idx_date} on {table_name}(
            guild_id,
            EXTRACT(MONTH FROM birthday),
            EXTRACT(DAY FROM birthday)
        );
        """).format(
            table_name=sql.Identifier(self._table_name),
            idx_get=sql.Identifier(f"idx_{self._table_name}_get_birthday"),
            idx_users=sql.Identifier(f"idx_{self._table_name}_users_birthday"),
            idx_date=sql.Identifier(f"idx_{self._table_name}_on_date"),
        )
        # Use db_client instead of _client to avoid getting an error
        _ = await self._db_client.post(query)
        self._table_exists = True
        _LOGGER.info(f"Table {self._table_name} created or already exists")

    @override
    async def add_birthday(
        self, user_id: UserID, guild_id: GuildID, birthday: date
    ) -> None:
        query = sql.SQL("""
            INSERT INTO {0} (user_id, guild_id, birthday)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, guild_id) DO NOTHING
            """).format(sql.Identifier(self._table_name))
        # Checking rows affected lets us not check for the birthday and save a query
        rows_affected = await self._client.post(query, (user_id, guild_id, birthday))
        if rows_affected == 0:
            raise BirthdayAlreadyExists(f"Birthday for user {user_id} already exists")
        _LOGGER.info(f"Added birthday for user {user_id} in guild {guild_id}")

    @override
    async def remove_birthday(self, user_id: UserID, guild_id: GuildID) -> None:
        query = sql.SQL("""
            DELETE FROM {0} WHERE user_id = %s AND guild_id = %s
        """).format(sql.Identifier(self._table_name))

        rows_affected = await self._client.post(query, (user_id, guild_id))
        if rows_affected < 1:
            raise BirthdayDoesNotExist()

    @override
    async def get_birthday(self, user_id: UserID, guild_id: GuildID) -> date | None:
        query = (
            sql.SQL("""
            SELECT birthday FROM {0}
            WHERE user_id = %s AND guild_id = %s
        """)
            .format(sql.Identifier(self._table_name))
            .as_string()
        )

        result = await self._client.get(query, (user_id, guild_id))
        if not result or not result[0] or not isinstance(result[0][0], date):
            return None
        return result[0][0]

    @override
    async def get_all_birthdays(self, user_id: UserID) -> list[date]:
        query = (
            sql.SQL("""
            SELECT DISTINCT birthday FROM {0}
            WHERE user_id = %s
        """)
            .format(sql.Identifier(self._table_name))
            .as_string()
        )
        result = await self._client.get(query, (user_id,))
        if not result:
            return []
        return [row[0] for row in result]

    @override
    async def get_birthdays(self, guild_id: GuildID) -> Mapping[int, date]:
        query = (
            sql.SQL("""
            SELECT user_id, birthday FROM {0}
            WHERE guild_id = %s
        """)
            .format(sql.Identifier(self._table_name))
            .as_string()
        )

        result = await self._client.get(query, (guild_id,))
        if not result:
            return {}
        try:
            return {row[0]: row[1] for row in result}
        except (ValueError, TypeError, IndexError) as e:
            raise BirthdayUnknownError("Somehow at least 2 rows did not exist") from e

    @override
    async def get_birthdays_on_date(
        self, guild_id: GuildID, date_: date
    ) -> Mapping[UserID, date]:
        query = (
            sql.SQL("""
            SELECT user_id, birthday FROM {0}
            WHERE guild_id = %s
            AND EXTRACT(DAY FROM birthday)=EXTRACT(DAY FROM %s)
            AND EXTRACT(MONTH FROM birthday)=EXTRACT(MONTH FROM %s)
        """)
            .format(sql.Identifier(self._table_name))
            .as_string()
        )

        result = await self._client.get(query, (guild_id, date_, date_))
        if not result:
            return {}
        try:
            return {row[0]: row[1] for row in result}
        except (ValueError, TypeError, IndexError) as e:
            raise BirthdayUnknownError("Somehow at least 2 rows did not exist") from e

    @override
    async def get_birthdays_today(self, guild_id: GuildID) -> Mapping[int, date]:
        query = (
            sql.SQL("""
            SELECT user_id, birthday FROM {0}
            WHERE guild_id = %s
            AND EXTRACT(DAY FROM birthday)=EXTRACT(DAY FROM CURRENT_DATE)
            AND EXTRACT(MONTH FROM birthday)=EXTRACT(MONTH FROM CURRENT_DATE)
        """)
            .format(sql.Identifier(self._table_name))
            .as_string()
        )

        result = await self._client.get(query, (guild_id,))
        if not result:
            return {}
        try:
            return {row[0]: row[1] for row in result}
        except (ValueError, TypeError, IndexError) as e:
            raise BirthdayUnknownError("Somehow at least 2 rows did not exist") from e
