from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import TypeAlias

from src.sql.errors import (
    AlreadyExists,
    MalformedSQLDataReceived,
    NotConnectedError,
    SQLError,
    SQLFailedMiserably,
)


class BirthdayError(SQLError):
    pass


class DBNotConnected(NotConnectedError, BirthdayError):
    pass


class BirthdayAlreadyExists(AlreadyExists, BirthdayError):
    pass


class BirthdayDoesNotExist(BirthdayError):
    pass


class BirthdayUnknownError(SQLFailedMiserably, BirthdayError):
    pass


class MalformedBirthdayDataReceived(MalformedSQLDataReceived, BirthdayError):
    pass


UserID: TypeAlias = int
GuildID: TypeAlias = int
Birthday: TypeAlias = date

@dataclass
class BirthdayConfig:
    """Represents the configuration for a guild's birthdays"""

    channel_id: int
    role_id: int | None = None


class BirthdayProvider(ABC):
    """
    Abstract class for birthdays

    Made to be used with guild specific birthdays
    Since these guilds will each also have their own birthday congratulation groups
    And users will be able to opt into their birthday being congratulated
    """

    @abstractmethod
    async def add_birthday(
        self, user_id: UserID, guild_id: GuildID, birthday: Birthday
    ) -> None:
        """
        Adds a birthday to a user specifically for that guild

        Args:
            user_id (UserID(int)): The ID of the user whose birthday is to be added
            guild_id (GuildID(int)): The ID of the guild to which the birthday is to be added
            birthday (Birthday(date)): The birthday to be added

        Raises:
            BirthdayAlreadyExists: If the birthday already exists
        """

    @abstractmethod
    async def remove_birthday(self, user_id: UserID, guild_id: GuildID) -> None:
        """Removes a users birthday from that guild

        Args:
            user_id (UserID(int)): The ID of the user whose birthday is to be removed
            guild_id (GuildID(int)): The ID of the guild from which the birthday is to be removed

        Raises:
            BirthdayDoesNotExist: If the birthday does not exist
        """

    @abstractmethod
    async def get_birthday(self, user_id: UserID, guild_id: GuildID) -> Birthday | None:
        """Get the birthday of a user for that specific guild

        Args:
            user_id (UserID(int)): The ID of the user whose birthday is to be retrieved
            guild_id (GuildID(int)): The ID of the guild from which the birthday is to be retrieved
        Returns:
            Birthday | None: The birthday of the user if it exists, otherwise None
        """

    @abstractmethod
    async def get_birthdays_for_user(self, user_id: UserID) -> list[Birthday]:
        """Gets every birthday the user saved across all guilds.

        Args:
            user_id (UserID(int)): The ID of the user whose birthdays are to be retrieved

        Returns:
            list[Birthday(date)]: A list of birthdays for the user across all guilds, **Empty** if none exist
        """

    @abstractmethod
    async def get_birthdays_in_guild(
        self, guild_id: GuildID
    ) -> Mapping[UserID, Birthday]:
        """Gets all birthdays for a specific guild.

        Args:
            guild_id (GuildID(int)): The ID of the guild whose birthdays are to be retrieved

        Returns:
            Mapping[UserID(int), Birthday(date)]: A mapping of user IDs to their birthdays for the specified guild, **Empty** if none exist
        """

    @abstractmethod
    async def get_birthdays_on_date(
        self, guild_id: GuildID, date_: Birthday
    ) -> Mapping[UserID, Birthday]:
        """Gets all birthdays for a specific guild on a specific date.

        Args:
            guild_id (GuildID(int)): The ID of the guild whose birthdays are to be retrieved
            date_ (Birthday(date)): The date on which to check for birthdays

        Returns:
            Mapping[UserID(int), Birthday(date)]: A mapping of user IDs to their birthdays for the specified guild on the specified date, **Empty** if none exist
        """

    @abstractmethod
    async def get_all_birthdays_on_date(
        self, date_: Birthday
    ) -> Mapping[GuildID, Mapping[UserID, Birthday]]:
        """Gets all birthdays across all guilds on a specific date.

        Args:
            date_ (Birthday(date)): The date on which to check for birthdays

        Returns:
            Mapping[GuildID(int), Mapping[UserID(int), Birthday(date)]]: A mapping of guild IDs to mappings of user IDs to their birthdays on the specified date, **Empty** if none exist
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
            BirthdayDoesNotExist: If no configuration exists for the specified guild
        """

    async def get_birthdays_today(self, guild_id: GuildID) -> Mapping[UserID, Birthday]:
        return await self.get_birthdays_on_date(guild_id, datetime.now(UTC).date())

    async def get_all_birthdays_today(
        self,
    ) -> Mapping[GuildID, Mapping[UserID, Birthday]]:
        return await self.get_all_birthdays_on_date(datetime.now(UTC).date())
