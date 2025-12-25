import logging
from typing import Final, Protocol

import discord

from src.sql.postgres import PostgresDBClient
from src.data.birthdays import BirthdayProvider
from src.data.providers.birthday_factory import BirthdayFactory
from src.sql.database import DatabaseClient
from src.sql.errors import NotConnectedError

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

    @property
    async def birthday_provider(self) -> BirthdayProvider:
        return await self._birthday_factory.create_birthday_provider


class DiscordClientWithDataManager(discord.Client):
    @property
    def data_manager(self) -> DataManager:
        ...

class DataManagerProvider(Protocol):
    @property
    def data_manager(self) -> DataManager:
        ...
