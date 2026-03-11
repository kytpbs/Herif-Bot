from datetime import datetime

import discord
from discord import app_commands

from Constants import BOT_ADMIN_SERVER_ID, CYAN, KYTPBS_TAG
from src.commands.command_group import CommandGroup
from src.Helpers.birthday_helpers import get_user_and_date_from_string
from src import client

birthdays = client.get_birthdays()

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
class BirthdayCommands(app_commands.Group, CommandGroup):
    @classmethod
    def get_commands(cls) -> list[discord.app_commands.Command | discord.app_commands.Group | discord.app_commands.ContextMenu]:
        return [
                cls(name="doğumgünü", description="Doğumgünü komutları"),
        ]

    @app_commands.command(name="dogumgunu_ekle", description="Doğumgününü eklemeni sağlar")
    async def add_birthday(self, interaction: discord.Interaction, day: str, month: str, year: str,
                           user: discord.Member = None):  # type: ignore
        if user is None:
            user = interaction.user  # type: ignore
        user_id = user.id
        date = datetime(int(year), int(month), int(day))
        date_string = str(date.year) + "-" + str(date.month) + "-" + str(date.day)
        if user_id in birthdays and birthdays[str(user_id)] is not None:
            await interaction.response.send_message(
                f"{user.mention} adlı kişinin doğum günü zaten '{birthdays[str(user_id)]}' olarak ayarlanmış " +
                f"Değiştirmek için lütfen {KYTPBS_TAG} kişisine ulaşın", ephemeral=True)
            return
        birthdays[str(user_id)] = date_string
        await interaction.response.send_message(
            f"{user.mention} adlı kişinin doğum günü '{date_string}' olarak ayarlandı")

    @app_commands.command(name="dogumgunu_goster", description="Kişinin doğumgününü gösterir")
    async def show_birthday(self, interaction: discord.Interaction, user: discord.Member):
        user_id = str(user.id)
        if birthdays.get(user_id) is not None:
            await interaction.response.send_message(f"{user.mention} adlı kişinin doğum günü '{birthdays[user_id]}'")
            return
        await interaction.response.send_message(f"{user.mention} adlı kişinin doğum günü kayıtlı değil",
                                                ephemeral=True)
    @app_commands.command(name="doğumgünü_sil",
                          description="Doğumgününü silmeni sağlar")
    async def delete_birthday(self, interaction: discord.Interaction, user: discord.Member):
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Sadece Sunucularda çalışır")
            return
        if (interaction.user != user and not interaction.user.guild_permissions.administrator) or user.guild.id != BOT_ADMIN_SERVER_ID:
            await interaction.response.send_message("Sadece Kendi Doğumgününü Silebilirsin", ephemeral=True)
            return
        user_id = str(user.id)
        if birthdays.get(user_id) is None:
            await interaction.response.send_message(f"{user.mention} adlı kişinin doğum günü zaten kayıtlı değil",
                                                    ephemeral=True)
            return
        del birthdays[user_id]
        await interaction.response.send_message(f"{user.mention} adlı kişinin doğum günü silindi")

    

    @app_commands.command(name="dogumgunu_listele", description="Doğumgünlerini listeler, sadece modlar kullanabilir")
    @app_commands.checks.has_permissions(administrator=True)
    async def list_birthday(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Bir hata oluştu, lütfen tekrar deneyin", ephemeral=True)
            return

        if interaction.user.guild_permissions.administrator is False:
            await interaction.response.send_message("Bu komutu kullanmak için gerekli iznin yok", ephemeral=True)
            return

        embed = discord.Embed(title="Doğumgünleri", description="Doğumgünleri", color=CYAN)
        new_list = get_user_and_date_from_string(birthdays)
        for user, date in new_list.items():
            embed.add_field(name=f"{user}:", value=f"{date}", inline=False)
        await interaction.response.send_message(embed=embed)

