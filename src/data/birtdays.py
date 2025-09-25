from abc import ABC, abstractmethod
from collections.abc import Mapping
from datetime import UTC, date, datetime
from typing import TypeAlias

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


class Birthdays(ABC):
    """
    Abstract class for birthdays

    Made to be used with guild specific birthdays
    Since these guilds will each also have their own birthday congratulion groups
    And users will be able to opt into their birthday being congratulated
    """

    @abstractmethod
    async def remove_birthday(self, user_id: UserID, guild_id: GuildID) -> None:
        pass

    @abstractmethod
    async def add_birthday(
        self, user_id: UserID, guild_id: GuildID, birthday: date
    ) -> None:
        pass

    @abstractmethod
    async def get_birthday(self, user_id: UserID, guild_id: GuildID) -> date | None:
        pass

    @abstractmethod
    async def get_all_birthdays(self, guild_id: GuildID) -> Mapping[UserID, date]:
        pass

    @abstractmethod
    async def get_birthdays_on_date(
        self, guild_id: GuildID, date_: date
    ) -> Mapping[UserID, date]:
        pass

    async def get_birthdays_today(self, guild_id: GuildID) -> Mapping[UserID, date]:
        return await self.get_birthdays_on_date(guild_id, datetime.now(UTC).date())
