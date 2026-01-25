from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeAlias

from src.sql.errors import (
    AlreadyExists,
    MalformedSQLDataReceived,
    NotConnectedError,
    SQLError,
    SQLFailedMiserably,
)


class ServerConfigError(SQLError):
    pass


class DBNotConnected(NotConnectedError, ServerConfigError):
    pass


class ServerConfigAlreadyExists(AlreadyExists, ServerConfigError):
    pass


class ServerConfigDoesNotExist(ServerConfigError):
    pass


class ServerConfigUnknownError(SQLFailedMiserably, ServerConfigError):
    pass


class MalformedServerConfigDataReceived(MalformedSQLDataReceived, ServerConfigError):
    pass


GuildID: TypeAlias = int


@dataclass
class BirthdayConfig:
    """Represents the configuration for a guild's birthdays"""

    channel_id: int
    role_id: int | None = None


@dataclass
class CustomizationConfig:
    """Represents the configuration for a guild's customizations (custom commands)"""

    is_enabled: bool = True


class ServerConfigProvider(ABC):
    """
    Abstract class for server/guild configuration

    Manages server-level settings like birthday configurations,
    logging configurations, and other guild-specific settings
    """

    @abstractmethod
    async def set_birthday_config(
        self, guild_id: GuildID, config: BirthdayConfig
    ) -> None:
        """Sets the birthday configuration for a specific guild, overwriting any existing configuration.

        <p>
        <b>Warning:
            Overwrites</b> any existing configuration for the guild if one exists.
        </p>

        Args:
            guild_id (GuildID(int)): The ID of the guild for which the configuration is to be set
            config (BirthdayConfig): The birthday configuration to be set for the guild
        """

    @abstractmethod
    async def get_birthday_config(self, guild_id: GuildID) -> BirthdayConfig | None:
        """Gets the guild's birthday configuration returning None if not setup

        Args:
            guild_id (GuildID): The ID of the guild whose birthday configuration is to be retrieved

        Returns:
            BirthdayConfig | None: The birthday configuration for the specified guild, or None if no configuration exists
        """

    @abstractmethod
    async def remove_birthday_config(self, guild_id: GuildID) -> None:
        """Removes the birthday configuration for a specific guild. Meaning disabling birthdays in that guild.

        Args:
            guild_id (GuildID(int)): The ID of the guild whose configuration is to be removed

        Raises:
            ServerConfigDoesNotExist: If no configuration exists for the specified guild
        """

    @abstractmethod
    async def set_customization_config(
        self, guild_id: GuildID, config: CustomizationConfig
    ) -> None:
        """Sets the customization configuration for a specific guild, overwriting any existing configuration.

        Args:
            guild_id (GuildID(int)): The ID of the guild for which the configuration is to be set
            config (CustomizationConfig): The customization configuration to be set for the guild
        """

    @abstractmethod
    async def get_customization_config(
        self, guild_id: GuildID
    ) -> CustomizationConfig | None:
        """Gets the guild's customization configuration returning None if not setup

        Args:
            guild_id (GuildID): The ID of the guild whose customization configuration is to be retrieved

        Returns:
            CustomizationConfig | None: The customization configuration for the specified guild, or None if no configuration exists (defaults to enabled)
        """

    @abstractmethod
    async def remove_customization_config(self, guild_id: GuildID) -> None:
        """Removes the customization configuration for a specific guild.

        Args:
            guild_id (GuildID(int)): The ID of the guild whose configuration is to be removed

        Raises:
            ServerConfigDoesNotExist: If no configuration exists for the specified guild
        """
