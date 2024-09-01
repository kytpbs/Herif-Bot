from typing import Optional

import discord
from discord import app_commands

import src.client as client
from src.download_commands import download_video_command

discord_client = client.get_client_instance()

tree = app_commands.CommandTree(discord_client)

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@tree.context_menu(name="Linkteki_Videoyu_Indir")
async def download_video_link(interaction: discord.Interaction, message: discord.Message):
    content = message.content
    await download_video_command(interaction, content)

@app_commands.allowed_installs(guilds=False, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@tree.context_menu(name="Linkteki_Videoyu_Gizlice_Indir")
async def download_video_link_hidden(interaction: discord.Interaction, message: discord.Message):
    content = message.content
    await download_video_command(interaction, content, is_ephemeral=True)


@tree.command(name="ping", description="Botun pingini gösterir")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong: {round(discord_client.latency * 1000)}ms")


@tree.command(name="video-indir", description="Paylaşılan linkteki videoyu paylaşır şuan-desteklenen: twitter, instagram, youtube")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def download_video(interaction: discord.Interaction, url: str, include_title: Optional[bool] = None):
    await download_video_command(interaction, url, include_title=include_title)


def get_tree_instance():
    return tree
