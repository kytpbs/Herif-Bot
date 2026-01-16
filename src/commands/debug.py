import discord
from discord import app_commands

from src.commands.command_group import CommandGroup, CommandList


@app_commands.command(name="ping", description="Botun pingini gösterir")
async def ping(interaction: discord.Interaction) -> None:
    _ = await interaction.response.send_message(
        f"Pong: {round(interaction.client.latency * 1000)}ms"
    )


class DebugCommands(CommandGroup):
    @classmethod
    def get_commands(cls) -> CommandList:
        return [
            ping,
        ]

