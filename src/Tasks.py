import logging
from datetime import date, datetime, time, timezone
from typing import Final, Mapping, Protocol

import discord
from discord.ext import tasks

from src.data.birthdays import GuildID
from src.data.data_manager import DataManagerProvider
from src.data.server_config import ServerConfigProvider
from src.file_handeler import delete_saved_attachments

_BIRTHDAY_LOGGER = logging.getLogger("Birthdays")
_ATTACHMENT_LOGGER = logging.getLogger("file_handler")


class BirthdayTasksContextProvider(DataManagerProvider, Protocol):
    """Protocol for a Discord client with required methods for birthday tasks."""

    def get_channel(
        self,
        id: int,  # pylint: disable=redefined-builtin # id is the name used in discord.py
        /,
    ) -> (
        discord.abc.GuildChannel | discord.Thread | discord.abc.PrivateChannel | None
    ): ...


async def _remove_role_from_all_members(guild: discord.Guild, role: discord.Role):
    for member in guild.members:
        if member.get_role(role.id) is not None:
            _BIRTHDAY_LOGGER.debug("Removing birthday role from member")
            await member.remove_roles(role)


async def _congratulate_birthday(
    general: discord.abc.Messageable,
    user: discord.Member | discord.User,
    birthday: date,
):
    age = datetime.now().year - birthday.year
    _ = await general.send(
        f"{user.mention} {age} yaşına girdi. Doğum günün kutlu olsun!"
    )


class Tasks:
    def __init__(self, client: BirthdayTasksContextProvider) -> None:
        self._client: Final = client

    def start(self):
        _ = self.check_birthdays.start()
        _ = self.clean_downloaded_attachments.start()

    async def _process_birthdays_check(
        self,
        guild_id: GuildID,
        birthdays: Mapping[int, date],
        server_config_provider: ServerConfigProvider,
    ):
        _BIRTHDAY_LOGGER.info("Checking birthdays")
        server_config = server_config_provider.get_config(guild_id)
        config = await server_config.birthday_config
        if config is None:
            _BIRTHDAY_LOGGER.info(
                "No birthday configuration found for guild %s, aborting birthday check",
                guild_id,
            )
            return

        congratulate_channel = self._client.get_channel(config.channel_id)

        if not isinstance(congratulate_channel, discord.abc.Messageable):
            _BIRTHDAY_LOGGER.error(
                "Could not find the birthday channel, aborting birthday check"
            )
            return

        role = (
            congratulate_channel.guild.get_role(config.role_id)
            if config.role_id
            else None
        )
        if not isinstance(role, discord.Role):
            _BIRTHDAY_LOGGER.warning(
                "Could not find birthday role, skipping, not giving birthdays"
            )

        # remove birthday role from members that have it.
        if role:
            await _remove_role_from_all_members(congratulate_channel.guild, role)

        for user_id, birthday in birthdays.items():
            user = congratulate_channel.guild.get_member(user_id)

            if not user:
                # user_id and guild_id are not exactly Private data, so logging is fine here
                # At least I think so
                _BIRTHDAY_LOGGER.error(
                    "Could not find user %s in guild %s, skipping birthday",
                    user_id,
                    guild_id,
                )
                # Someone probably left the guild
                continue

            await _congratulate_birthday(congratulate_channel, user, birthday)

            if role:
                await user.add_roles(role)

    @tasks.loop(
        time=time(hour=6, minute=30, tzinfo=timezone.utc)
    )  # 9.30 for +3 timezone
    async def check_birthdays(self):
        birthday_provider = await self._client.data_manager.birthday_provider
        server_config_provider = await self._client.data_manager.server_config_provider

        todays_birthdays = await birthday_provider.get_all_birthdays_today()
        for guild_id, birthdays in todays_birthdays.items():
            await self._process_birthdays_check(
                guild_id, birthdays, server_config_provider
            )

    @staticmethod
    @tasks.loop(hours=168)  # 1 week
    async def clean_downloaded_attachments():
        await delete_saved_attachments()
