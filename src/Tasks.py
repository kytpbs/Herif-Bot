import os
from datetime import datetime, time, timezone

import discord
from discord.ext import tasks

from Constants import BIRTHDAY_ROLE_ID, GENERAL_CHAT_ID
from src import logging_system
from src.birthday_helpers import get_user_and_date_from_string


class task_list:
  @staticmethod
  @tasks.loop(time=time(hour=6, minute=30, tzinfo=timezone.utc))  # 9.30 for +3 timezone
  async def check_birthdays():
    import client as Client
    client = Client.get_client_instance()
    birthdays = Client.get_birthdays()
    logging_system.log("Checking birthdays")
    general = client.get_channel(GENERAL_CHAT_ID)
    if not isinstance(general, discord.TextChannel):
      raise ValueError(f"Kanal Bulunamadı aranan id: {GENERAL_CHAT_ID}")
    rol = general.guild.get_role(BIRTHDAY_ROLE_ID)
    today = datetime.now()
    usable_dict = get_user_and_date_from_string(birthdays)

    if not isinstance(rol, discord.Role):
      raise RuntimeError(f"Rol Bulunamadı aranan id: {BIRTHDAY_ROLE_ID}")
    if not isinstance(general, discord.TextChannel):
      raise RuntimeError(f"Kanal Bulunamadı aranan id: {GENERAL_CHAT_ID}")

    # remove birthday role from members that have it.
    for member in client.get_all_members():
      if member.get_role(BIRTHDAY_ROLE_ID) is not None:
        print(f"{member} adlı kişinin doğum günü rolü kaldırılıyor")
        await member.remove_roles(rol)

    for user, birthday in usable_dict.items():
      if birthday.month == today.month and birthday.day == today.day:
        age = today.year - birthday.year
        await user.add_roles(rol)  # add birthday role to user.
        await general.send(f"{user.mention} {age} yaşına girdi. Doğum günün kutlu olsun!")

  @staticmethod
  @tasks.loop(hours=72)
  async def clear_cache():
    logging_system.log("clearing cache", logging_system.DEBUG)
    folder_directory = f"{os.getcwd()}/cache"
    for file in os.listdir(folder_directory):
      os.remove(f"{folder_directory}/{file}")


def start_tasks():
  task_list.check_birthdays.start()