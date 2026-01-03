from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Awaitable, TypeAlias

from src.sql.errors import (
    AlreadyExists,
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
    async def remove_birthday(self, user_id: UserID, guild_id: GuildID) -> None:
        pass

    @abstractmethod
    async def add_birthday(
        self, user_id: UserID, guild_id: GuildID, birthday: Birthday
    ) -> None:
        pass

    @abstractmethod
    async def get_birthday(self, user_id: UserID, guild_id: GuildID) -> Birthday | None:
        pass

    @abstractmethod
    async def get_all_birthdays(self, user_id: UserID) -> list[Birthday]:
        """Get all distinct birthdays for a user"""

    @abstractmethod
    async def get_birthdays(self, guild_id: GuildID) -> Mapping[UserID, Birthday]:
        """Get all distinct birthdays for a guild"""
        pass

    @abstractmethod
    async def get_birthdays_on_date(
        self, guild_id: GuildID, date_: Birthday
    ) -> Mapping[UserID, Birthday]:
        pass

    @abstractmethod
    async def get_all_birthdays_on_date(
        self, date_: Birthday
    ) -> Mapping[GuildID, Mapping[UserID, Birthday]]:
        pass
        # TODO: do this...

    @abstractmethod
    async def set_birthday_config(
        self, guild_id: GuildID, config: BirthdayConfig
    ) -> None:
        pass

    @abstractmethod
    async def get_birthday_config(self, guild_id: GuildID) -> BirthdayConfig | None:
        pass

    async def get_birthdays_today(self, guild_id: GuildID) -> Mapping[UserID, Birthday]:
        return await self.get_birthdays_on_date(guild_id, datetime.now(UTC).date())
