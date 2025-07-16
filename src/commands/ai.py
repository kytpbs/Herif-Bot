import discord
from discord import app_commands

from src.llm_system import gpt
from src.llm_system.llm_errors import LLMError


@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
class AiCommands(app_commands.Group):
    @app_commands.command(name="soru", description="bota bir soru sor")
    async def chatgpt(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer(ephemeral=False)
        try:
            answer = await gpt.interaction_chat(interaction, message, include_history=False)
        except LLMError:
            await interaction.followup.send("Bir şey ters gitti, lütfen tekrar deneyin", ephemeral=True)
            raise
        await interaction.followup.send(answer)

    @app_commands.command(name="sohbet", description="Botun sohbete katılmasını sağlar! (eski mesaj okur!)")
    async def question(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer(ephemeral=False)
        try:
            answer = await gpt.interaction_chat(interaction, message)
        except LLMError:
            await interaction.followup.send("Bir hata oluştu, lütfen tekrar deneyin", ephemeral=True)
            raise # re-raise the error so that the error is logged
        await interaction.followup.send(answer)


