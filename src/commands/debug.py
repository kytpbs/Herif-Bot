import discord
from discord import app_commands

from src.commands.command_group import CommandGroup


class DebugCommands(CommandGroup):
    @classmethod
    def get_commands(cls) -> list[discord.app_commands.Command | discord.app_commands.Group | discord.app_commands.ContextMenu]:
        return [
            ping,
         ]

@app_commands.command(name="ping", description="Botun pingini gösterir")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong: {round(interaction.client.latency * 1000)}ms")


