import logging
import discord

from src.Helpers.twitter_helpers import convert_paths_to_discord_files
from src.downloading_system import get_downloader


async def download_video_command(interaction: discord.Interaction, url: str, is_ephemeral: bool = False):
    #TODO: add better error handling then just catching all exceptions
    downloader = get_downloader(url)
    if downloader is None:
        await interaction.response.send_message("Bu link desteklenmiyor", ephemeral=True)
        logging.info("Found an unsupported link: %s", url)
        return

    await interaction.response.defer(ephemeral=is_ephemeral)

    try:
        attachments = downloader.download_video_from_link(url)
    except Exception as e:
        await interaction.followup.send("Bir şey ters gitti... lütfen tekrar deneyin", ephemeral=True)
        raise e # re-raise the exception so we can see what went wrong
    file_paths = [attachment.path for attachment in attachments]
    if len(attachments) == 0:
        await interaction.followup.send("Bir şeyler ters gitti, lütfen tekrar deneyin", ephemeral=True)
        return
    content = " + ".join(filter(None, [attachment.caption for attachment in attachments])) or "Video Downloaded"
    await interaction.followup.send(content, files=convert_paths_to_discord_files(file_paths))
