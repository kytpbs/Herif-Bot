import logging
from typing import Final

from src.data.birthdays import BirthdayProvider
from src.data.providers.birthday_json import BirthdayJson
from src.data.providers.birthday_sql import BirthdaySQL
from src.sql.database import DatabaseClient
from src.sql.errors import NotConnectedError

_LOGGER = logging.getLogger("Birthdays")


class BirthdayFactory:
    def __init__(self, client: DatabaseClient | None):
        """

        Args:
            client (DatabaseClient | None): The database client to use for SQL provider, if None, JSON provider will be used
        """
        self._birthday_provider: BirthdayProvider | None = None
        self._db_client: Final = client

    @property
    async def create_birthday_provider(self) -> BirthdayProvider:
        if self._birthday_provider is None:
            self._birthday_provider = await self._create_birthday_provider()
        return self._birthday_provider

    async def _create_birthday_provider(self) -> BirthdayProvider:
        _LOGGER.debug("Creating Birthday Provider")
        try:
            return await self._get_sql_provider()
        except NotConnectedError:
            return self._get_json_provider()

    def _get_json_provider(self) -> BirthdayProvider:
        return BirthdayJson()

    async def _get_sql_provider(self) -> BirthdayProvider:
        if self._db_client is None:
            _LOGGER.error("No database client provided for SQL birthday provider")
            raise NotConnectedError(
                "No database client provided for SQL birthday provider"
            )
        db_client = self._db_client
        return await BirthdaySQL.create(db_client)
