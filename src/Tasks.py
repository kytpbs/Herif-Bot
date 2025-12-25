import logging
from datetime import date, datetime, time, timezone
from typing import Final, Protocol

import discord
from discord.ext import tasks

from Constants import BIRTHDAY_ROLE_ID, GENERAL_CHAT_ID
from src.data.data_manager import DataManagerProvider
from src.file_handeler import delete_saved_attachments

_BIRTHDAY_LOGGER = logging.getLogger("Birthdays")


class BirthdayTasksContextProvider(DataManagerProvider, Protocol):
    """Protocol for a Discord client with required methods for birthday tasks."""

    def get_channel(
        self,
        id: int,  # pylint: disable=redefined-builtin # id is the name used in discord.py
        /,
    ) -> (
        discord.abc.GuildChannel | discord.Thread | discord.abc.PrivateChannel | None
    ): ...


async def _remove_role_from_all_members(guild: discord.Guild, role_id: int):
    role = guild.get_role(role_id)
    if not isinstance(role, discord.Role):
        _BIRTHDAY_LOGGER.error(f"Rol Bulunamadı aranan id: {role_id}")
        return

    for member in guild.members:
        if member.get_role(role_id) is not None:
            _BIRTHDAY_LOGGER.info(f"{member} adlı kişinin doğum günü rolü kaldırılıyor")
            await member.remove_roles(role)


async def _congratulate_birthday(
    general: discord.abc.Messageable,
    user: discord.Member | discord.User,
    birthday: date,
):
    age = datetime.now().year - birthday.year
    _ = await general.send(f"{user.mention} {age} yaşına girdi. Doğum günün kutlu olsun!")


class Tasks:
    def __init__(self, client: BirthdayTasksContextProvider) -> None:
        self._client: Final = client

    def start(self):
        _ = self.check_birthdays.start()
        _ = self.clean_downloaded_attachments.start()

    @tasks.loop(
        time=time(hour=6, minute=30, tzinfo=timezone.utc)
    )  # 9.30 for +3 timezone
    async def check_birthdays(self):
        birthday_provider = await self._client.data_manager.birthday_provider

        _BIRTHDAY_LOGGER.info("Checking birthdays")
        general = self._client.get_channel(GENERAL_CHAT_ID)

        if not isinstance(general, discord.abc.Messageable):
            _BIRTHDAY_LOGGER.error(f"Kanal Bulunamadı aranan id: {GENERAL_CHAT_ID}")
            return

        rol = general.guild.get_role(BIRTHDAY_ROLE_ID)
        if not isinstance(rol, discord.Role):
            _BIRTHDAY_LOGGER.error(f"Rol Bulunamadı aranan id: {BIRTHDAY_ROLE_ID}")

        # remove birthday role from members that have it.
        if rol is not None:
            await _remove_role_from_all_members(general.guild, rol.id)

        birthdays = await birthday_provider.get_birthdays_today(general.guild.id)

        for user_id, birthday in birthdays.items():
            user = general.guild.get_member(user_id)

            if not user:
                _BIRTHDAY_LOGGER.error(f"Kullanıcı Bulunamadı aranan id: {user_id}")
                continue

            await _congratulate_birthday(general, user, birthday)

            if rol:
                await user.add_roles(rol)  # add birthday role to user. if it exists

    @staticmethod
    @tasks.loop(hours=168)  # 1 week
    async def clean_downloaded_attachments():
        _BIRTHDAY_LOGGER.info("cleaning downloaded attachments")
        await delete_saved_attachments()
