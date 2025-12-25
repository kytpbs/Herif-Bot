import logging
from itertools import islice

import discord
from discord import app_commands

from Constants import CYAN
from src.data.data_manager import DiscordClientWithDataManager
from src.commands.command_group import CommandGroup, CommandList
from src.data.customizations import CustomizationError

_LOGGER = logging.getLogger("Commands.Customization")


@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
class CustomizationCommands(app_commands.Group, CommandGroup):
    @classmethod
    def get_commands(cls) -> CommandList:
        return [
            cls(
                name="özel",
                description="Bota özel komutlar ekleyip görmen için komutlar",
            ),
        ]

    @app_commands.command(
        name="olustur",
        description="botun senin ayarladığın mesajlara cevap verebilmesini sağlar",
    )
    async def create_command(
        self,
        interaction: discord.Interaction[DiscordClientWithDataManager],
        text: str,
        answer: str,
    ):
        if not interaction.guild_id:
            _ = await interaction.response.send_message(
                "Bu komut sadece sunucularda kullanılabilir", ephemeral=True
            )
            return

        customs_provider = await interaction.client.data_manager.customization_provider
        response = await customs_provider.get_response(interaction.guild_id, text)

        if response:
            _ = await interaction.response.send_message(
                f"Bu mesaja zaten bir cevap var: {response}, "
                + "lütfen başka bir mesaj deneyin"
                if response.added_by_user_id != interaction.user.id
                else "değiştirmek için önce olan cevabı silmelisiniz",
                ephemeral=True,
            )
            return

        await customs_provider.create_custom_command(
            interaction.guild_id, text, answer, interaction.user.id
        )
        embed = discord.Embed(
            title="Cevap Oluşturuldu",
            description=f"'_{text}_': '_{answer}_' adlı cevap oluşturuldu",
            color=CYAN,
        )

        _ = await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="cevaplar", description="Bütün özel eklenmiş cevapları gösterir"
    )
    async def answers(self, interaction: discord.Interaction[DiscordClientWithDataManager]):
        if not interaction.guild_id:
            _ = await interaction.response.send_message(
                "Bu komut sadece sunucularda kullanılabilir", ephemeral=True
            )
            return
        customs_provider = await interaction.client.data_manager.customization_provider
        responses = await customs_provider.get_all_custom_commands(
            interaction.guild_id, limit=26
        )  # limit to 26 to check if there are more than 25
        if not responses:
            _ = await interaction.response.send_message(
                "Bu sunucuda özel eklenmiş cevap yok", ephemeral=True
            )
            return

        embed = discord.Embed(title="Özel Cevaplar", color=CYAN)
        embed.description = (
            "Özel eklenmiş cevaplar"
            if len(responses) <= 24
            else "Özel eklenmiş cevapların bir kısmı (gösterilen 24 cevap) \n\n"
        )

        for trigger, response in islice(responses.items(), 24):
            _ = embed.add_field(name=trigger, value=response, inline=False)
        _ = await interaction.response.send_message(embed=embed)

    async def _delete_autocomplete(
        self,
        interaction: discord.Interaction[DiscordClientWithDataManager],
        current: str,
    ) -> list[app_commands.Choice[str]]:
        if not interaction.guild_id or not isinstance(interaction.user, discord.Member):
            return []
        customs_provider = await interaction.client.data_manager.customization_provider
        responses = await customs_provider.get_all_custom_commands(interaction.guild_id)
        choices = [
            app_commands.Choice(
                name=f"{cmd}: {response}"[:97] + ("..." if len(cmd + str(response)) > 97 else ""),
                value=cmd,
            )
            for cmd, response in responses.items()
            if (
                current.lower() in cmd.lower()
                and (
                    interaction.user.guild_permissions.administrator
                    or response.added_by_user_id == interaction.user.id
                )
            )
        ]
        return choices

    @app_commands.autocomplete(trigger=_delete_autocomplete)
    @app_commands.command(name="sil", description="Özel eklenmiş bir cevabı siler")
    async def delete_command(
        self, interaction: discord.Interaction[DiscordClientWithDataManager], trigger: str
    ):
        if not interaction.guild_id or not isinstance(interaction.user, discord.Member):
            _ = await interaction.response.send_message(
                "Bu komut sadece sunucularda kullanılabilir", ephemeral=True
            )
            return
        customs_provider = await interaction.client.data_manager.customization_provider

        response = await customs_provider.get_response(interaction.guild_id, trigger)

        if response is None:
            _ = await interaction.response.send_message(
                f"'_{trigger}_' için cevap bulunamadı", ephemeral=True
            )
            return

        if (
            not interaction.user.guild_permissions.administrator
            and response.added_by_user_id != interaction.user.id
        ):
            _ = await interaction.response.send_message(
                f"{trigger} mesajına olan cevabı silme yetkiniz yok", ephemeral=True
            )
            return

        try:
            await customs_provider.delete_custom_command(interaction.guild_id, trigger)
        except CustomizationError as e:
            _LOGGER.error(f"Özel cevap silinirken hata oluştu: {e}")
            _ = await interaction.response.send_message(
                f"'{trigger}' adlı cevabı silerken bir hata oluştu", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Cevap Silindi",
            description=f"'_{trigger}_: _{response}_' adlı cevap silindi",
            color=CYAN,
        )
        _ = await interaction.response.send_message(embed=embed)
