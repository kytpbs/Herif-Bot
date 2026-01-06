import os
from collections.abc import Mapping
from typing import Final, cast

from psycopg import sql
from typing_extensions import override

from src.data.customizations import (
    Command,
    CustomCommand,
    CustomizationAlreadyExists,
    CustomizationDoesNotExist,
    CustomizationProvider,
    DBNotConnected,
    GuildID,
    MalformedCustomizationDataReceived,
    Response,
    UserID,
)
from src.sql.database import DatabaseClient


class CustomizationSQL(CustomizationProvider):
    @classmethod
    async def create(cls, db_client: DatabaseClient) -> "CustomizationSQL":
        instance = cls(db_client)
        await instance.start_up()
        return instance

    def __init__(self, db_client: DatabaseClient):
        self._db_client: Final = db_client
        self._table_exists: bool = False
        self._table_name: str = os.getenv("CUSTOMIZATION_TABLE_NAME", "customizations")

    @property
    def _client(self):
        if not self._table_exists:
            raise DBNotConnected("Database not initialized. Call start_up() first.")
        return self._db_client

    async def start_up(self):
        await self._create_table_if_not_exists()

    async def _create_table_if_not_exists(self):
        query = sql.SQL("""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            guild_id BIGINT NOT NULL,
            command_input TEXT NOT NULL,
            response TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            added_by_user_id BIGINT,
            UNIQUE(guild_id, command_input)
        );
        
        CREATE INDEX IF NOT EXISTS {idx_guild} ON {table_name}(guild_id);
        CREATE INDEX IF NOT EXISTS {idx_guild_command} ON {table_name}(guild_id, command_input);
        """).format(
            table_name=sql.Identifier(self._table_name),
            idx_guild=sql.Identifier(f"{self._table_name}_guild_idx"),
            idx_guild_command=sql.Identifier(f"{self._table_name}_guild_command_idx"),
        )
        _ = await self._db_client.post(query)
        self._table_exists = True

    @override
    async def create_custom_command(
        self,
        guild_id: GuildID,
        command_input: Command,
        response: Response,
        added_by_user_id: UserID | None = None,
    ) -> None:
        query = sql.SQL("""
        INSERT INTO {table_name} (guild_id, command_input, response, added_by_user_id)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (guild_id, command_input) DO NOTHING
        """).format(table_name=sql.Identifier(self._table_name))
        count = await self._client.post(
            query, (guild_id, command_input, response, added_by_user_id)
        )
        if count == 0:
            raise CustomizationAlreadyExists()

    @override
    async def delete_custom_command(
        self, guild_id: GuildID, command_input: Command
    ) -> None:
        query = sql.SQL("""
        DELETE FROM {table_name}
        WHERE guild_id = %s AND command_input = %s
        """).format(table_name=sql.Identifier(self._table_name))
        count = await self._client.post(query, (guild_id, command_input))
        if count == 0:
            raise CustomizationDoesNotExist()

    @override
    async def get_response(
        self, guild_id: GuildID, command_input: Command
    ) -> CustomCommand | None:
        query = sql.SQL("""
        SELECT response, added_by_user_id FROM {table_name}
        WHERE guild_id = %s AND command_input = %s
        """).format(table_name=sql.Identifier(self._table_name))
        result = await self._client.get(query, (guild_id, command_input))
        if (
            not result
            or not result[0]
            or not isinstance(result[0][0], str)
            or not isinstance(result[0][1], int)
        ):
            return None
        return CustomCommand(
            guild_id=guild_id,
            command_input=command_input,
            response=result[0][0],
            added_by_user_id=result[0][1],
        )

    @override
    async def get_all_custom_commands(
        self, guild_id: GuildID, limit: int | None = None
    ) -> Mapping[Command, CustomCommand]:
        query = sql.SQL("""
        SELECT command_input, response, added_by_user_id FROM {table_name}
        WHERE guild_id = %s
        LIMIT %s
        """).format(table_name=sql.Identifier(self._table_name))
        result = await self._client.get(query, (guild_id, limit))
        if not result:
            return {}
        try:
            return {
                row[0]: CustomCommand(
                    guild_id=guild_id,
                    command_input=cast(str, row[0]),
                    response=cast(str, row[1]),
                    added_by_user_id=cast(int, row[2]),
                )
                for row in result
            }
        except (ValueError, TypeError, IndexError) as e:
            raise MalformedCustomizationDataReceived() from e

    @override
    async def get_creator(
        self, guild_id: GuildID, command_input: Command
    ) -> UserID | None:
        query = sql.SQL("""
        SELECT added_by_user_id FROM {table_name}
        WHERE guild_id = %s AND command_input = %s
    """).format(table_name=sql.Identifier(self._table_name))
        result = await self._client.get(query, (guild_id, command_input))
        if not result or not result[0] or not isinstance(result[0][0], int):
            return None
        return result[0][0]
