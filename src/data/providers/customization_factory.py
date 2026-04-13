import logging
from typing import Final

from src.data.customizations import CustomizationProvider
from src.data.providers.customization_json import CustomizationJson
from src.data.providers.customization_sql import CustomizationSQL
from src.sql.database import DatabaseClient
from src.sql.errors import NotConnectedError

_LOGGER = logging.getLogger("Customizations")


class CustomizationFactory:
    def __init__(self, client: DatabaseClient | None):
        """

        Args:
            client (DatabaseClient | None): The database client to use for SQL provider, if None, JSON provider will be used
        """
        self._customization_provider: CustomizationProvider | None = None
        self._db_client: Final = client
    async def create_customization_provider(self) -> CustomizationProvider:
        _LOGGER.debug("Creating Customization Provider")
        try:
            return await self._get_sql_provider()
        except NotConnectedError:
            return self._get_json_provider()

    def _get_json_provider(self) -> CustomizationProvider:
        return CustomizationJson()

    async def _get_sql_provider(self) -> CustomizationProvider:
        if self._db_client is None:
            _LOGGER.error("No database client provided for SQL customization provider")
            raise NotConnectedError(
                "No database client provided for SQL customization provider"
            )
        db_client = self._db_client
        return await CustomizationSQL.create(db_client)
