from collections.abc import MutableMapping
from datetime import date
import logging
from typing import Final

from typing_extensions import override

from src.data.birthdays import (
    Birthday,
    BirthdayAlreadyExists,
    BirthdayConfig,
    BirthdayDoesNotExist,
    BirthdayProvider,
    GuildID,
    UserID,
)
from src.Helpers.helper_functions import DiskDict

UserBirthdays = MutableMapping[UserID, Birthday]
BirthdayGuilds = MutableMapping[GuildID, UserBirthdays]

BirthdayConfigs = MutableMapping[GuildID, BirthdayConfig]

_LOGGER = logging.getLogger("BirthdayJson")


class BirthdayJson(BirthdayProvider):
    def __init__(self):
        self.guild_birthdays: Final[BirthdayGuilds] = DiskDict("birthday_guild.json")
        self.configs: Final[BirthdayConfigs] = DiskDict("birthday_config.json")

    @override
    async def remove_birthday(self, user_id: UserID, guild_id: GuildID):
        birthdays = self.guild_birthdays.setdefault(guild_id, {})
        if user_id not in birthdays:
            raise BirthdayDoesNotExist()
        del birthdays[user_id]
        _LOGGER.debug("Removed birthday for user %s in guild %s", user_id, guild_id)

    @override
    async def add_birthday(
        self, user_id: UserID, guild_id: GuildID, birthday: Birthday
    ):
        birthdays = self.guild_birthdays.setdefault(guild_id, {})
        if user_id in birthdays:
            raise BirthdayAlreadyExists()
        birthdays[user_id] = birthday
        _LOGGER.debug("Added birthday for user %s in guild %s", user_id, guild_id)

    @override
    async def get_birthday(self, user_id: UserID, guild_id: GuildID) -> date | None:
        birthdays = self.guild_birthdays.get(guild_id, {})
        return birthdays.get(user_id)

    @override
    async def get_birthdays_for_user(self, user_id: UserID) -> list[Birthday]:
        # get a user's birthdays in every possible guild
        # O(n) where n is the number of guilds, but that's fine since this is
        # only for backup and should normally be provided by SQL providers
        all_birthdays: list[Birthday] = []
        for birthdays in self.guild_birthdays.values():
            birthday = birthdays.get(user_id)
            if birthday is not None:
                all_birthdays.append(birthday)
        return all_birthdays

    @override
    async def get_birthdays_in_guild(self, guild_id: GuildID) -> UserBirthdays:
        return self.guild_birthdays.get(guild_id, {})

    @override
    async def get_birthdays_on_date(
        self, guild_id: GuildID, date_: date
    ) -> UserBirthdays:
        birthdays = self.guild_birthdays.get(guild_id, {})
        return {
            user_id: birthday
            for user_id, birthday in birthdays.items()
            if birthday.day == date_.day and birthday.month == date_.month
        }

    @override
    async def set_birthday_config(
        self, guild_id: GuildID, config: BirthdayConfig
    ) -> None:
        self.configs[guild_id] = config
        _LOGGER.debug(f"Added birthday config for guild {guild_id}")

    @override
    async def get_all_birthdays_on_date(self, date_: date) -> BirthdayGuilds:
        return {
            guild_id: matching_birthdays
            for guild_id in self.guild_birthdays.keys()
            if (matching_birthdays := await self.get_birthdays_on_date(guild_id, date_))
        }

    @override
    async def remove_birthday_config(self, guild_id: GuildID) -> None:
        if guild_id not in self.configs:
            _LOGGER.debug(f"No birthday config found for guild {guild_id} to remove")
            raise BirthdayDoesNotExist()
        del self.configs[guild_id]
        _LOGGER.debug(f"Removed birthday config for guild {guild_id}")

    @override
    async def get_birthday_config(self, guild_id: GuildID) -> BirthdayConfig | None:
        return self.configs.get(guild_id)
