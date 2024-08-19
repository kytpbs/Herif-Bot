import logging
import discord

from src.downloading_system import get_downloader

def _convert_paths_to_discord_files(paths: list[str]) -> list[discord.File]:
    return [discord.File(path) for path in paths]


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
        file_paths = [attachment.path for attachment in attachments]
        discord_files = _convert_paths_to_discord_files(file_paths)
    except Exception as e:
        await interaction.followup.send("Bir şey ters gitti... lütfen tekrar deneyin", ephemeral=True)
        raise e # re-raise the exception so we can see what went wrong
    if len(attachments) == 0:
        await interaction.followup.send("Videoyu Bulamadım, lütfen daha sonra tekrar deneyin ya da hatayı bildirin", ephemeral=True)
        return
    content = " + ".join(filter(None, [attachment.caption for attachment in attachments])) or f"Video{'s' if len(attachments) > 1 else ''} Downloaded"
    await interaction.followup.send(content, files=discord_files, ephemeral=is_ephemeral)
