from collections.abc import Mapping, MutableMapping
from datetime import date
from typing_extensions import override

from src.data.birtdays import (
    Birthday,
    BirthdayAlreadyExists,
    BirthdayDoesNotExist,
    BirthdayProvider,
    GuildID,
    UserID,
)
from src.Helpers.helper_functions import DiskDict

UserBirthdays = MutableMapping[UserID, Birthday]
BirthdayGuilds = MutableMapping[GuildID, UserBirthdays]


class BirthdayJsonDB(BirthdayProvider):
    def __init__(self):
        self.guild_birthdays: BirthdayGuilds = DiskDict("birthday_guild.json")

    @override
    async def remove_birthday(self, user_id: UserID, guild_id: GuildID):
        birthdays = self.guild_birthdays.setdefault(guild_id, {})
        if user_id not in birthdays:
            raise BirthdayDoesNotExist()
        del birthdays[user_id]

    @override
    async def add_birthday(self, user_id: UserID, guild_id: GuildID, birthday: Birthday):
        birthdays = self.guild_birthdays.setdefault(guild_id, {})
        if user_id in birthdays:
            raise BirthdayAlreadyExists()
        birthdays[user_id] = birthday

    @override
    async def get_birthday(self, user_id: UserID, guild_id: GuildID) -> date | None:
        birthdays = self.guild_birthdays.get(guild_id, {})
        return birthdays.get(user_id)

    @override
    async def get_all_birthdays(self, user_id: UserID) -> list[Birthday]:
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
    async def get_birthdays(self, guild_id: GuildID) -> Mapping[UserID, Birthday]:
        return self.guild_birthdays.get(guild_id, {})

    @override
    async def get_birthdays_on_date(
        self, guild_id: GuildID, date_: date
    ) -> Mapping[UserID, Birthday]:
        birthdays = self.guild_birthdays.get(guild_id, {})
        return {
            user_id: birthday
            for user_id, birthday in birthdays.items()
            if birthday.day == date_.day and birthday.month == date_.month
        }
