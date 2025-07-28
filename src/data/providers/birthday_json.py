from collections.abc import Mapping, MutableMapping
from datetime import date

from src.data.birtdays import (
    BirthdayAlreadyExists,
    BirthdayDoesNotExist,
    Birthdays,
    GuildID,
    UserID,
)
from src.Helpers.helper_functions import DiskDict

UserBirthdays = MutableMapping[UserID, date]
BirthdayGuilds = MutableMapping[GuildID, UserBirthdays]


class BirthdayJsonDB(Birthdays):
    def __init__(self):
        self.guild_birthdays: BirthdayGuilds = DiskDict("birthday_guild.json")

    async def remove_birthday(self, user_id: UserID, guild_id: GuildID):
        birthdays = self.guild_birthdays.setdefault(guild_id, {})
        if user_id not in birthdays:
            raise BirthdayDoesNotExist()
        del birthdays[user_id]

    async def add_birthday(self, user_id: UserID, guild_id: GuildID, birthday: date):
        birthdays = self.guild_birthdays.setdefault(guild_id, {})
        if user_id in birthdays:
            raise BirthdayAlreadyExists()
        birthdays[user_id] = birthday

    async def get_birthday(self, user_id: UserID, guild_id: GuildID) -> date | None:
        birthdays = self.guild_birthdays.get(guild_id, {})
        return birthdays.get(user_id)

    async def get_all_birthdays(self, guild_id: GuildID) -> Mapping[UserID, date]:
        return self.guild_birthdays.get(guild_id, {})

    async def get_birthdays_on_date(
        self, guild_id: GuildID, date_: date
    ) -> Mapping[UserID, date]:
        birthdays = self.guild_birthdays.get(guild_id, {})
        return {
            user_id: birthday
            for user_id, birthday in birthdays.items()
            if birthday.day == date_.day and birthday.month == date_.month
        }
