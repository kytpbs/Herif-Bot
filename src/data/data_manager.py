from abc import ABC
import logging
from typing import Final, Protocol

import discord

from src.data.birthdays import BirthdayProvider
from src.data.customizations import CustomizationProvider
from src.data.providers.birthday_factory import BirthdayFactory
from src.data.providers.customization_factory import CustomizationFactory
from src.data.providers.server_config_factory import ServerConfigFactory
from src.data.server_config import ServerConfigProvider
from src.sql.database import DatabaseClient
from src.sql.errors import NotConnectedError
from src.sql.postgres import PostgresDBClient

_LOGGER = logging.getLogger("DataManager")


class DataManager:
    """
    Central place for all dynamic data that the codebase uses.
    """

    def __init__(self):
        self._db_client: DatabaseClient | None = None
        try:
            self._db_client = PostgresDBClient()
        except NotConnectedError:
            _LOGGER.warning(
                "Database not connected, will pass None to all data providers"
            )
        self._birthday_factory: Final = BirthdayFactory(self._db_client)
        self._customization_factory: Final = CustomizationFactory(self._db_client)
        self._server_config_factory: Final = ServerConfigFactory(self._db_client)

        self._birthday_provider: BirthdayProvider | None = None
        self._customization_provider: CustomizationProvider | None = None
        self._server_config_provider: ServerConfigProvider | None = None

    @property
    async def birthday_provider(self) -> BirthdayProvider:
        if self._birthday_provider is None:
            self._birthday_provider = await self._birthday_factory.create_birthday_provider()
        return self._birthday_provider

    @property
    async def customization_provider(self) -> CustomizationProvider:
        if self._customization_provider is None:
            self._customization_provider = await self._customization_factory.create_customization_provider()
        return self._customization_provider

    @property
    async def server_config_provider(self) -> ServerConfigProvider:
        if self._server_config_provider is None:
            self._server_config_provider = await self._server_config_factory.create_server_config_provider()
        return self._server_config_provider


# Special typing for discord.Client with DataManager
class DiscordClientWithDataManager(ABC, discord.Client):
    @property
    def data_manager(self) -> DataManager: ...


# Protocol for classes that provide access to DataManager
class DataManagerProvider(Protocol):
    @property
    def data_manager(self) -> DataManager: ...
