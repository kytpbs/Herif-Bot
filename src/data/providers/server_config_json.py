import logging
from collections.abc import MutableMapping
from typing import Final

from typing_extensions import override

from src.data.server_config import (
    BirthdayConfig,
    CustomizationConfig,
    GuildID,
    ServerConfigDoesNotExist,
    ServerConfigProvider,
)
from src.Helpers.helper_functions import DiskDict

BirthdayConfigs = MutableMapping[GuildID, BirthdayConfig]
CustomizationConfigs = MutableMapping[GuildID, CustomizationConfig]

_LOGGER = logging.getLogger("ServerConfigJson")


class ServerConfigJson(ServerConfigProvider):
    def __init__(self):
        self.birthday_configs: Final[BirthdayConfigs] = DiskDict("birthday_config.json")
        self.customization_configs: Final[CustomizationConfigs] = DiskDict(
            "customization_config.json"
        )

    @override
    async def set_birthday_config(
        self, guild_id: GuildID, config: BirthdayConfig
    ) -> None:
        self.birthday_configs[guild_id] = config
        _LOGGER.debug("Added birthday config for guild %s", guild_id)

    @override
    async def remove_birthday_config(self, guild_id: GuildID) -> None:
        if guild_id not in self.birthday_configs:
            _LOGGER.debug("No birthday config found for guild %s to remove", guild_id)
            raise ServerConfigDoesNotExist()
        del self.birthday_configs[guild_id]
        _LOGGER.debug("Removed birthday config for guild %s", guild_id)

    @override
    async def get_birthday_config(self, guild_id: GuildID) -> BirthdayConfig | None:
        return self.birthday_configs.get(guild_id)

    @override
    async def set_customization_config(
        self, guild_id: GuildID, config: CustomizationConfig
    ) -> None:
        self.customization_configs[guild_id] = config
        _LOGGER.debug(
            "Set customization config for guild %s to enabled=%s",
            guild_id,
            config.is_enabled,
        )

    @override
    async def remove_customization_config(self, guild_id: GuildID) -> None:
        if guild_id not in self.customization_configs:
            _LOGGER.debug(
                "No customization config found for guild %s to remove", guild_id
            )
            raise ServerConfigDoesNotExist()
        del self.customization_configs[guild_id]
        _LOGGER.debug("Removed customization config for guild %s", guild_id)

    @override
    async def get_customization_config(self, guild_id: GuildID) -> CustomizationConfig:
        return self.customization_configs.get(guild_id, CustomizationConfig())
