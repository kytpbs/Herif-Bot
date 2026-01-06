from datetime import date
import functools
from typing import Literal, cast

import discord
from discord import app_commands

from Constants import CYAN
from src.data.data_manager import DiscordClientWithDataManager
from src.data.birthdays import BirthdayConfig, BirthdayDoesNotExist
from src.commands.command_group import CommandGroup, CommandList

DataManagerInteraction = discord.Interaction[DiscordClientWithDataManager]


def _assert_guild_membered(
    interaction: DataManagerInteraction,
) -> tuple[discord.Member, int] | tuple[None, None]:
    if not isinstance(interaction.user, discord.Member) or not interaction.guild_id:
        _ = interaction.response.send_message(
            "Bu komut sadece sunucularda kullanılabilir", ephemeral=True
        )
        return None, None
    return (interaction.user, interaction.guild_id)


@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
class BirthdayCommands(app_commands.Group, CommandGroup):
    @classmethod
    def get_commands(cls) -> CommandList:
        return [
            cls(name="doğumgünü", description="Doğumgünü komutları"),
        ]


    # Config Setup Commands
    @app_commands.command(
        name="ayarlar",
        description="Bir birthday'a ait ayarları ayarlamak için kullanılır",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def birthday_config(
        self,
        interaction: DataManagerInteraction,
        congratulate_channel: discord.TextChannel | None = None,
        congratulate_role: discord.Role | None = None,
    ):
        birthday_provider = await interaction.client.data_manager.birthday_provider
        user, guild_id = _assert_guild_membered(interaction)
        if not user or not guild_id:
            return

        if not user.guild_permissions.administrator:
            _ = await interaction.response.send_message(
                "Bu komutu kullanmak için gerekli iznin yok", ephemeral=True
            )
            return

        pre_existing_config = None

        if not congratulate_channel and not (
            pre_existing_config := await birthday_provider.get_birthday_config(guild_id)
        ):
            _ = await interaction.response.send_message(
                "Birthday ayarları ayarlanmadı, lütfen bir channel ve bir role belirtin",
                ephemeral=True,
            )
            return

        channel_id = (
            congratulate_channel.id
            if congratulate_channel
            # LSP is confused about the possibility of pre_existing_config being None
            # It is not possible for it to be None when congratulate_channel is None
            else pre_existing_config.channel_id  # pyright: ignore[reportOptionalMemberAccess]
        )

        role_id = congratulate_role.id if congratulate_role else None

        await birthday_provider.set_birthday_config(
            guild_id, BirthdayConfig(channel_id, role_id)
        )
        _ = await interaction.response.send_message("Doğumgünü ayarları güncellendi")

    async def _birthday_autocomplete(
        self,
        interaction: DataManagerInteraction,
        current: str,
    ) -> list[app_commands.Choice[int]]:
        return await self._birthday_atr_autocomplete(interaction, current)

    async def _birthday_atr_autocomplete(
        self,
        interaction: DataManagerInteraction,
        current: str,
        attr: Literal["day", "month", "year"] = "day",
    ) -> list[app_commands.Choice[int]]:
        birthday_provider = await interaction.client.data_manager.birthday_provider

        try:
            birthdays = await birthday_provider.get_birthdays_for_user(
                interaction.user.id
            )
        except BirthdayDoesNotExist:
            return []

        return sorted(
            # Use set comprehension to remove duplicates
            {
                app_commands.Choice(
                    name=str(cast(int, getattr(birthday, attr))),
                    value=cast(int, getattr(birthday, attr)),
                )
                for birthday in birthdays
                if current in str(cast(int, getattr(birthday, attr)))
            },
            key=lambda x: x.value,
        )

    @app_commands.command(
        name="dogumgunu_ekle", description="Doğumgününü eklemeni sağlar"
    )
    @app_commands.autocomplete(
        day=functools.update_wrapper(
            functools.partial(_birthday_atr_autocomplete, attr="day"),
            _birthday_autocomplete,
        ),
        month=functools.update_wrapper(
            functools.partial(_birthday_atr_autocomplete, attr="month"),
            _birthday_autocomplete,
        ),
        year=functools.update_wrapper(
            functools.partial(_birthday_atr_autocomplete, attr="year"),
            _birthday_autocomplete,
        ),
    )
    async def add_birthday(
        self,
        interaction: DataManagerInteraction,
        day: app_commands.Range[int, 1, 31],
        month: app_commands.Range[int, 1, 12],
        year: app_commands.Range[int, 1900, date.today().year],
        user: discord.Member | None = None,
    ):
        """Add a birthday for a user, or for yourself if no user is provided.

        Args:
            interaction (DataManagerInteraction)
            day (int): _day of the month_ (1-31)
            month (int): _month of the year_ (1-12)
            year (int): _year_ (e.g., 1990)
            user (discord.Member | None, optional): _The user whose birthday is being added. Defaults to adding it for the interaction user.
        """
        birthday_provider = await interaction.client.data_manager.birthday_provider
        interaction_user, interaction_guild_id = _assert_guild_membered(interaction)
        if not interaction_user or not interaction_guild_id:
            return

        if user is None:
            user = interaction_user

        try:
            birthday_date = date(year, month, day)
        except ValueError:
            _ = await interaction.response.send_message(
                "Geçersiz tarih girdin, lütfen tekrar dene", ephemeral=True
            )
            return

        birthday = await birthday_provider.get_birthday(user.id, interaction_guild_id)

        if birthday:
            _ = await interaction.response.send_message(
                f"{user.mention} adlı kişinin doğum günü zaten '{birthday.strftime('%d/%m/%Y')}' olarak ayarlanmış "
                + "Değiştirmek için önce doğum gününü silmelisin",
                ephemeral=True,
            )
            return

        await birthday_provider.add_birthday(
            user.id, interaction_guild_id, birthday_date
        )

        _ = await interaction.response.send_message(
            f"{user.mention} adlı kişinin doğum günü '{birthday_date.strftime('%d/%m/%Y')}' olarak ayarlandı"
        )

    @app_commands.command(
        name="dogumgunu_goster", description="Kişinin doğumgününü gösterir"
    )
    async def show_birthday(
        self,
        interaction: DataManagerInteraction,
        user: discord.Member | None = None,
    ):
        birthday_provider = await interaction.client.data_manager.birthday_provider
        interaction_user, interaction_guild_id = _assert_guild_membered(interaction)
        if not interaction_user or not interaction_guild_id:
            return
        user = user or interaction_user

        birthday = await birthday_provider.get_birthday(user.id, interaction_guild_id)
        if birthday:
            _ = await interaction.response.send_message(
                f"{user.mention} adlı kişinin doğum günü '{birthday.strftime('%d/%m/%Y')}'"
            )
            return
        _ = await interaction.response.send_message(
            f"{user.mention} adlı kişinin doğum günü kayıtlı değil", ephemeral=True
        )

    @app_commands.command(
        name="doğumgünü_sil", description="Doğumgününü silmeni sağlar"
    )
    async def delete_birthday(
        self,
        interaction: DataManagerInteraction,
        user: discord.Member | None = None,
    ):
        interaction_user, interaction_guild_id = _assert_guild_membered(interaction)
        if not interaction_user or not interaction_guild_id:
            return
        user = user or interaction_user
        if (
            interaction_user != user
            and not interaction_user.guild_permissions.administrator
        ):
            _ = await interaction.response.send_message(
                "Sadece Kendi Doğumgününü Silebilirsin", ephemeral=True
            )
            return

        birthday_provider = await interaction.client.data_manager.birthday_provider

        try:
            await birthday_provider.remove_birthday(user.id, interaction_guild_id)
            _ = await interaction.response.send_message(
                f"{user.mention} adlı kişinin doğum günü silindi"
            )
        except BirthdayDoesNotExist:
            _ = await interaction.response.send_message(
                f"{user.mention} adlı kişinin doğum günü bu sunucuda zaten kayıtlı değil",
                ephemeral=True,
            )

    @app_commands.command(
        name="dogumgunu_listele",
        description="Doğumgünlerini listeler, sadece modlar kullanabilir",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def list_birthday(self, interaction: DataManagerInteraction):
        interaction_user, interaction_guild_id = _assert_guild_membered(interaction)
        if not interaction_user or not interaction_guild_id:
            return
        birthday_provider = await interaction.client.data_manager.birthday_provider

        if interaction_user.guild_permissions.administrator is False:
            _ = await interaction.response.send_message(
                "Bu komutu kullanmak için gerekli iznin yok", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Doğumgünleri", description="Doğumgünleri", color=CYAN
        )

        birthdays = await birthday_provider.get_birthdays_in_guild(interaction_guild_id)

        for user, birthday in birthdays.items():
            _ = embed.add_field(name=f"{user}:", value=f"{birthday}", inline=False)
        _ = await interaction.response.send_message(embed=embed)


    @app_commands.command(
        name="ayarlar_sil",
        description="Sunucuda doğum günü kutlamalarını devre dışı bırakır",
    )
    @app_commands.checks.has_permissions(administrator=True) #! Admin only
    async def remove_config(
        self,
        interaction: DataManagerInteraction,
    ):
        birthday_provider = await interaction.client.data_manager.birthday_provider
        user, guild_id = _assert_guild_membered(interaction)
        if not user or not guild_id:
            return

        try:
            await birthday_provider.remove_birthday_config(guild_id)
            _ = await interaction.response.send_message("Birthday ayarları silindi")
        except BirthdayDoesNotExist:
            _ = await interaction.response.send_message(
                "Birthday ayarları zaten silinmiş", ephemeral=True
            )