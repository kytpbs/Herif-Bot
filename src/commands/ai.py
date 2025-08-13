import discord
from discord import app_commands

from src.commands.command_group import CommandGroup
from src.llm_system import gpt
from src.llm_system.llm_errors import LLMError


@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
class AiCommands(app_commands.Group, CommandGroup):
    @classmethod
    def get_commands(cls):
        return [
            cls(name="zeki", description="Botu zeki yapan komutlar"),
            story_writer,
        ]

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

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.command(name="feridun_abi", description="Yine seks hikayesi mi yazıyorsun feridun abi?")
async def story_writer(interaction: discord.Interaction, message: str):
    await interaction.response.defer(ephemeral=False)
    try:
        answer = await gpt.story_writer(interaction, message)
    except LLMError:
        await interaction.followup.send("Bir şey ters gitti, lütfen tekrar deneyin", ephemeral=True)
        raise
    if len(answer) < 2000:
        await interaction.followup.send(answer)
        return
    for i in range(0, len(answer), 2000):
        await interaction.followup.send(answer[i:i + 2000])

