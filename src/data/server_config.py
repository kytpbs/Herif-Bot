from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Final, TypeAlias

from async_lru import alru_cache

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


class ServerConfigAccessor:
    """
    Lazy accessor for server configuration that only queries the database when properties are accessed.

    Provides a clean API with async properties while maintaining performance through lazy loading.
    Caches results within the same instance to avoid duplicate queries.
    """

    def __init__(self, guild_id: GuildID, provider: "ServerConfigProvider"):
        self._guild_id: Final = guild_id
        self._provider: Final = provider
        self._cache: Final[dict[str, BirthdayConfig | CustomizationConfig | None]] = {}

    @property
    @alru_cache(ttl=60 * 5)  # Cache results for 5 minutes
    async def birthday_config(self) -> BirthdayConfig | None:
        """
        Lazily fetches and caches the birthday configuration for this guild.

        Returns:
            BirthdayConfig | None: The birthday configuration, or None if not configured
        """
        return await self._provider.get_birthday_config(self._guild_id)

    @property
    @alru_cache(ttl=60 * 5)  # Cache results for 5 minutes
    async def customization_config(self) -> CustomizationConfig:
        """
        Lazily fetches and caches the customization configuration for this guild.

        Returns:
            CustomizationConfig: The customization configuration, with default values if not configured
        """
        return await self._provider.get_customization_config(self._guild_id)


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
        """Gets the guild's birthday configuration returning None if admin has not set up birthdays.

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
        """Sets the customization configuration for a specific guild, overwriting any existing configuration
        except if role_id is not given and channel_id is given, in which case role_id will be set to previous value.

        Args:
            guild_id (GuildID(int)): The ID of the guild for which the configuration is to be set
            config (CustomizationConfig): The customization configuration to be set for the guild
        """

    @abstractmethod
    async def get_customization_config(self, guild_id: GuildID) -> CustomizationConfig:
        """Gets the guild's customization configuration, returning default values if not setup.

        Args:
            guild_id (GuildID): The ID of the guild whose customization configuration is to be retrieved

        Returns:
            CustomizationConfig: The customization configuration for the specified guild, with default values if no configuration exists (defaults to enabled)
        """

    @abstractmethod
    async def remove_customization_config(self, guild_id: GuildID) -> None:
        """Removes the customization configuration for a specific guild.

        Args:
            guild_id (GuildID(int)): The ID of the guild whose configuration is to be removed

        Raises:
            ServerConfigDoesNotExist: If no configuration exists for the specified guild
        """

    def get_config(self, guild_id: GuildID) -> ServerConfigAccessor:
        """
        Returns a convenient object all server configurations for the specified guild.

        All configurations are lazily loaded when accessed. And will be heavily cached for subsequent accesses.

        See:
            :meth:`ServerConfigProvider.get_birthday_config` to get birthday server configs without caching and lazy loading
            :meth:`ServerConfigProvider.get_customization_config` to get customization server configs without caching and lazy loading

        Args:
            guild_id (GuildID): The ID of the guild whose configuration accessor is to be created

        Returns:
            ServerConfigAccessor: A lazy accessor for server configurations

        Example:
            >>> config = server_config_provider.get_config(guild_id)
            >>> birthday_cfg = await config.birthday_config  # Only queries birthday_config table
            >>> custom_cfg = await config.customization_config  # Only queries customization_config table
        """
        return ServerConfigAccessor(guild_id, self)
