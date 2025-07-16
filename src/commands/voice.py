import discord
from discord import app_commands

from src.voice import voice_commands
from src.voice.old_message_holder import add_message_to_be_deleted


class VoiceCommands(app_commands.Group):
    @app_commands.command(name="çal", description="Youtube'dan bir şey çalmanı sağlar")
    async def cal(self, interaction: discord.Interaction, arat: str):
        await interaction.response.defer()
        response = await voice_commands.play(interaction, arat)
        message = await interaction.followup.send(
            """
            _Bu özellik `/çal` ile aynı şeyi yapıyor, lütfen bundan sonra `/ses çal` yerine '/çal' kullanın._
            _Eğer düğmeler bozulur ise: `/çalan` komutunu kullanabilirsin_\n\n
            """ + response.message,
            embed=response.embed,
            ephemeral=response.ephemeral,
            view=response.view,
            wait=True,
        )
        add_message_to_be_deleted(interaction.guild_id, message)




app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@app_commands.command(name="çal")
async def new_play(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    response = await voice_commands.play(interaction, url)
    message = await interaction.followup.send(response.message + "\n\n _Eğer düğmeler bozulur ise: `/çalan` komutunu kullan_", embed=response.embed, ephemeral=response.ephemeral, view=response.view, wait=True)
    add_message_to_be_deleted(interaction.guild_id, message)


