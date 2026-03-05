import os
from typing_extensions import override

from psycopg import sql

from src.data.server_config import (
    BirthdayConfig,
    CustomizationConfig,
    ServerConfigProvider,
    ServerConfigDoesNotExist,
    DBNotConnected,
    GuildID,
)

from src.sql.database import LOGGER, DatabaseClient

_LOGGER = LOGGER.getChild("ServerConfigSQL")


class ServerConfigSQL(ServerConfigProvider):
    @classmethod
    async def create(cls, client: DatabaseClient) -> "ServerConfigSQL":
        instance = cls(client)
        await instance.start_up()
        return instance

    def __init__(self, client: DatabaseClient):
        self._db_client: DatabaseClient = client
        self._table_exists: bool = False
        self._birthday_config_table_name: str = os.getenv(
            "BIRTHDAY_CONFIG_TABLE_NAME", "birthday_config"
        )
        self._customization_config_table_name: str = os.getenv(
            "CUSTOMIZATION_CONFIG_TABLE_NAME", "customization_config"
        )

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

        CREATE TABLE IF NOT EXISTS {birthday_config_table_name}(
            guild_id BIGINT PRIMARY KEY,
            channel_id BIGINT NOT NULL,
            role_id BIGINT
        );

        CREATE TABLE IF NOT EXISTS {customization_config_table_name}(
            guild_id BIGINT PRIMARY KEY,
            is_enabled BOOLEAN NOT NULL DEFAULT TRUE
        );
        """).format(
            birthday_config_table_name=sql.Identifier(self._birthday_config_table_name),
            customization_config_table_name=sql.Identifier(self._customization_config_table_name),
        )
        # Use db_client instead of _client to avoid getting an error
        _ = await self._db_client.post(query)
        self._table_exists = True
        _LOGGER.info(f"Table {self._birthday_config_table_name} created or already exists")

    @override
    async def set_birthday_config(
        self, guild_id: GuildID, config: BirthdayConfig
    ) -> None:
        query = sql.SQL("""
            INSERT INTO {0} (guild_id, channel_id, role_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (guild_id) DO UPDATE SET
                channel_id = %s,
                role_id = COALESCE(EXCLUDED.role_id, {0}.role_id)
        """).format(sql.Identifier(self._birthday_config_table_name))

        _ = await self._client.post(
            query,
            (
                guild_id,
                config.channel_id,
                config.role_id,
                config.channel_id,
            ),
        )
        _LOGGER.debug("Added birthday config for guild %s", guild_id)

    @override
    async def remove_birthday_config(self, guild_id: GuildID) -> None:
        query = sql.SQL("""
            DELETE FROM {0} WHERE guild_id = %s
        """).format(sql.Identifier(self._birthday_config_table_name))

        rows_affected = await self._client.post(query, (guild_id,))
        if rows_affected < 1:
            _LOGGER.debug("No birthday config found for guild %s to remove", guild_id)
            raise ServerConfigDoesNotExist()
        _LOGGER.debug("Removed birthday config for guild %s", guild_id)

    @override
    async def get_birthday_config(self, guild_id: GuildID) -> BirthdayConfig | None:
        query = sql.SQL("""
            SELECT channel_id, role_id FROM {0}
            WHERE guild_id = %s
        """).format(sql.Identifier(self._birthday_config_table_name))
        result = await self._client.get(query, (guild_id,))
        if (
            not result
            or not result[0]
            or not isinstance(result[0][0], int)
            or not isinstance(result[0][1], int | None)
        ):
            return None
        return BirthdayConfig(result[0][0], result[0][1])

    @override
    async def set_customization_config(
        self, guild_id: GuildID, config: CustomizationConfig
    ) -> None:
        query = sql.SQL("""
            INSERT INTO {0} (guild_id, is_enabled)
            VALUES (%s, %s)
            ON CONFLICT (guild_id) DO UPDATE SET
                is_enabled = %s
        """).format(sql.Identifier(self._customization_config_table_name))

        _ = await self._client.post(
            query,
            (guild_id, config.is_enabled, config.is_enabled),
        )
        _LOGGER.debug("Set customization config for guild %s to enabled=%s", guild_id, config.is_enabled)

    @override
    async def get_customization_config(self, guild_id: GuildID) -> CustomizationConfig:
        query = sql.SQL("""
            SELECT is_enabled FROM {0}
            WHERE guild_id = %s
        """).format(sql.Identifier(self._customization_config_table_name))
        result = await self._client.get(query, (guild_id,))
        if not result or not result[0] or not isinstance(result[0][0], bool):
            return CustomizationConfig()
        return CustomizationConfig(result[0][0])

    @override
    async def remove_customization_config(self, guild_id: GuildID) -> None:
        query = sql.SQL("""
            DELETE FROM {0} WHERE guild_id = %s
        """).format(sql.Identifier(self._customization_config_table_name))

        rows_affected = await self._client.post(query, (guild_id,))
        if rows_affected < 1:
            _LOGGER.debug("No customization config found for guild %s to remove", guild_id)
            raise ServerConfigDoesNotExist()
        _LOGGER.debug("Removed customization config for guild %s", guild_id)
