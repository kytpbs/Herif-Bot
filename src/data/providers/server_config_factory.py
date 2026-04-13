import logging
from typing import Final

from src.data.providers.server_config_json import ServerConfigJson
from src.data.providers.server_config_sql import ServerConfigSQL
from src.data.server_config import ServerConfigProvider
from src.sql.database import DatabaseClient
from src.sql.errors import NotConnectedError

_LOGGER = logging.getLogger("ServerConfig")


class ServerConfigFactory:
    def __init__(self, client: DatabaseClient | None):
        """

        Args:
            client (DatabaseClient | None): The database client to use for SQL provider, if None, JSON provider will be used
        """
        self._server_config_provider: ServerConfigProvider | None = None
        self._db_client: Final = client

    async def create_server_config_provider(self) -> ServerConfigProvider:
        if self._server_config_provider is None:
            self._server_config_provider = await self._create_server_config_provider()
        return self._server_config_provider

    async def _create_server_config_provider(self) -> ServerConfigProvider:
        _LOGGER.debug("Creating Server Config Provider")
        try:
            return await self._get_sql_provider()
        except NotConnectedError:
            return self._get_json_provider()

    def _get_json_provider(self) -> ServerConfigProvider:
        return ServerConfigJson()

    async def _get_sql_provider(self) -> ServerConfigProvider:
        if self._db_client is None:
            _LOGGER.error("No database client provided for SQL server config provider")
            raise NotConnectedError(
                "No database client provided for SQL server config provider"
            )
        db_client = self._db_client
        return await ServerConfigSQL.create(db_client)
