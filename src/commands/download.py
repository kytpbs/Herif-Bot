import discord
from discord import app_commands

from src.commands.command_group import CommandGroup
from src.download_system.download_commands import download_video_command

class DownloadCommands(CommandGroup):
    @classmethod
    def get_commands(cls):
        return [
            download_video,
            download_video_link,
            download_video_link_hidden,
        ]


@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.context_menu(name="Linkteki_Videoyu_Indir")
async def download_video_link(interaction: discord.Interaction, message: discord.Message):
    content = message.content
    await download_video_command(interaction, content)

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.context_menu(name="Linkteki_Videoyu_Gizlice_Indir")
async def download_video_link_hidden(interaction: discord.Interaction, message: discord.Message):
    content = message.content
    await download_video_command(interaction, content, is_ephemeral=True)

@app_commands.command(name="video-indir", description="Paylaşılan linkteki videoyu paylaşır şuan-desteklenen: twitter, instagram, youtube")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def download_video(interaction: discord.Interaction, url: str, include_title: bool | None = None):
    await download_video_command(interaction, url, include_title=include_title)



