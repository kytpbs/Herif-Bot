import logging

import discord
from discord import app_commands

from src.commands.ai import AiCommands
from src.commands.birthday import BirthdayCommands
from src.commands.customization import CustomizationCommands
from src.commands.debug import DebugCommands
from src.commands.download import DownloadCommands
from src.commands.messages import MessagesCommands
from src.commands.voice import VoiceCommands


def create_tree(client: discord.Client):
    tree = app_commands.CommandTree(client)
    setup_error_handler(tree)
    return tree

async def _on_tree_error(interaction: discord.Interaction, error: Exception):
    logging.error("An error occurred while processing an interaction", exc_info=error)
    if interaction.response.is_done():
        await interaction.followup.send("Bilinmeyen bir hata, lütfen tekrar deneyin", ephemeral=True)
    else:
        await interaction.response.send_message("Bilinmeyen bir hata, lütfen tekrar deneyin", ephemeral=True)


def setup_error_handler(tree: app_commands.CommandTree):
    tree.error(_on_tree_error)

def setup_commands(tree: app_commands.CommandTree):
    AiCommands.register_commands(tree)
    BirthdayCommands.register_commands(tree)
    CustomizationCommands.register_commands(tree)
    DebugCommands.register_commands(tree)
    DownloadCommands.register_commands(tree)
    MessagesCommands.register_commands(tree)
    VoiceCommands.register_commands(tree)

