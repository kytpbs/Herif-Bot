import logging
from datetime import datetime, time, timedelta, timezone

import discord
from discord.ext import tasks

from Constants import BIRTHDAY_ROLE_ID, GENERAL_CHAT_ID, DEFAULT_GUILD_ID
import birthday_system
from src.file_handeler import delete_saved_attachments
from src.Helpers.birthday_helpers import get_user_and_date_from_string


async def _remove_birthdays_from_users_in_guild(guild: discord.Guild):
    role = guild.get_role(BIRTHDAY_ROLE_ID)
    if role is None:
        logging.error(f"Role not found for id {BIRTHDAY_ROLE_ID}")
        return
    for member in guild.members:
        if role in member.roles:
            await member.remove_roles(role)

async def _remove_birthdays_from_users(client: discord.Client):
    guilds = client.guilds
    for guild in guilds:
        await _remove_birthdays_from_users_in_guild(guild)

async def birthday_check():
    from src.client import get_client_instance # pylint: disable=import-outside-toplevel # circular import
    client = get_client_instance()
    # remove birthday role from all users before adding it to the ones that have birthday today
    await _remove_birthdays_from_users(client)
    birthday_system.find_users_birthday(datetime.now().date())
    birthdays = birthday_system.find_user_and_guild_from_birthday(datetime.now().date())
    for user, guild_id in birthdays:
        if guild_id is None:
            logging.error(f"Guild id not found for user {user}")
            guild_id = DEFAULT_GUILD_ID

        guild = client.get_guild(guild_id)
        if guild is None:
            logging.error(f"Guild not found for id {guild_id}")
            continue
        member = guild.get_member(user)
        if member is None:
            logging.error(f"Member not found for user {user}")
            continue
        general = client.get_general_channel(guild)
        if general is None:
            logging.error(f"General channel not found for guild {guild}")
            continue
        role = guild.get_role(BIRTHDAY_ROLE_ID)
        if role is None:
            logging.error(f"Role not found for id {BIRTHDAY_ROLE_ID}")
            continue
        await member.add_roles(role)
        await general.send(f"Doğum günün kutlu olsun {member.mention}! 🎉")

class task_list:
    @staticmethod
    @tasks.loop(
        time=time(hour=6, minute=30, tzinfo=timezone(timedelta(hours=3)))
    )  # 9.30 for +3 timezone
    async def check_birthdays():
        import src.client as discord_client

        client = discord_client.get_client_instance()
        birthdays = discord_client.get_birthdays()
        logging.info("Checking birthdays")
        general = client.get_channel(GENERAL_CHAT_ID)

        if not isinstance(general, discord.TextChannel):
            logging.error(f"Kanal Bulunamadı aranan id: {GENERAL_CHAT_ID}")
            return

        rol = general.guild.get_role(BIRTHDAY_ROLE_ID)
        today = datetime.now()
        usable_dict = get_user_and_date_from_string(
            birthdays, guild_to_check=general.guild
        )

        if not isinstance(rol, discord.Role):
            logging.error(f"Rol Bulunamadı aranan id: {BIRTHDAY_ROLE_ID}")
        if not isinstance(general, discord.TextChannel):
            raise RuntimeError(f"Kanal Bulunamadı aranan id: {GENERAL_CHAT_ID}")

        # remove birthday role from members that have it.
        if rol is not None:
            for member in client.get_all_members():
                if member.get_role(BIRTHDAY_ROLE_ID) is not None:
                    logging.info(f"{member} adlı kişinin doğum günü rolü kaldırılıyor")
                    await member.remove_roles(rol)

        for user, birthday in usable_dict.items():
            if birthday.month == today.month and birthday.day == today.day:
                age = today.year - birthday.year
                await general.send(
                    f"{user.mention} {age} yaşına girdi. Doğum günün kutlu olsun!"
                )
                if rol is not None and isinstance(user, discord.Member):
                    await user.add_roles(rol)  # add birthday role to user. if it exists

    @staticmethod
    @tasks.loop(hours=168) # 1 week
    async def clean_downloaded_attachments():
        logging.info("cleaning downloaded attachments")
        await delete_saved_attachments()


def start_tasks():
    task_list.check_birthdays.start()
    task_list.clean_downloaded_attachments.start()
