import asyncio
import logging

import discord

from src.download_system.caption_view import CaptionView
from src.download_system.downloader import (
    VIDEO_RETURN_TYPE,
    AbstractClassUsedError,
    DownloadFailedError,
    NoVideoFoundError,
    VideoDownloader,
)
from src.download_system.downloaders.other import UnknownAlternateDownloader
from src.download_system.downloading_system import get_downloader, get_url_from_text


def _convert_paths_to_discord_files(paths: list[str]) -> list[discord.File]:
    return [discord.File(path) for path in paths]


def _get_shortest_punctuation_index(caption: str) -> int | None:
    # check if we have a punctuation mark in the caption
    dot = caption.find(".")
    comma = caption.find(",")
    question_mark = caption.find("?")
    exclamation_mark = caption.find("!")
    filtered_list = list(
        filter(lambda x: x != -1, [dot, comma, question_mark, exclamation_mark])
    )
    if len(filtered_list) == 0:
        return None
    return min(filtered_list)


def _get_shortened_caption(caption: str) -> str:
    # check if we have a punctuation mark in the caption
    caption = caption.split("\n", maxsplit=1)[0]

    punctuation_index = _get_shortest_punctuation_index(caption)
    if punctuation_index:
        return caption[: punctuation_index + 1]
    return caption[:100]


def _get_caption_and_view(
    real_caption: str, include_title: bool | None
) -> tuple[str | None, discord.ui.View]:
    shortened_caption = _get_shortened_caption(real_caption) + " ***...***"
    view = discord.utils.MISSING

    if include_title is False:
        caption = None

    elif include_title is True:
        caption = real_caption

    elif len(shortened_caption) < len(real_caption):
        view = CaptionView(real_caption, shortened_caption)
        caption = shortened_caption
    else:
        caption = real_caption

    return caption, view


def _process_url(url: str) -> str:
    if "youtube.com" in url and "shorts/" in url:
        url = url.split("?")[0]
        url = url.replace("shorts/", "watch?v=")

    # add any more replacements or other modifications here
    return url


async def get_details(
    downloader: type[VideoDownloader], url: str, interaction: discord.Interaction
) -> VIDEO_RETURN_TYPE | None:
    """Gets the details of the video from the downloader.

    Args:
        downloader (type[VideoDownloader]): the downloader to use
        url (str): the url to download the video from
        interaction (discord.Interaction): the interaction to edit with ``interaction.response.edit_message``

    Returns:
        VIDEO_RETURN_TYPE | None: the details of the video, or None if the download failed
    """
    try:
        return await downloader.download_video_from_link(url)
    except DownloadFailedError:
        await interaction.followup.send(
            "Video indirilirken başarısız olundu, hata raporu alındı. Lütfen daha sonra tekrar deneyin",
            ephemeral=True,
        )
        logging.exception("Failed Downloading Link: %s", url)
        return
    except NoVideoFoundError:
        await interaction.followup.send(
            "Linkte bir video bulamadım, linkte **video** olduğuna emin misin?",
            ephemeral=True,
        )
        logging.exception("Couldn't find link on url %s", url)
        return
    except AbstractClassUsedError:
        await interaction.followup.send(
            "Bir şeyler ÇOK ters gitti, hata raporu alındı.", ephemeral=True
        )
        logging.exception("An abstract class was used, this should not happen")
        return
    except Exception as e:
        await interaction.followup.send(
            "Bilinmeyen bir hata oluştu, lütfen tekrar deneyin", ephemeral=True
        )
        raise e


async def _convert_to_discord_files(
    interaction: discord.Interaction, attachments: VIDEO_RETURN_TYPE
) -> list[discord.File]:
    try:
        file_paths = [attachment.path for attachment in attachments]
        return _convert_paths_to_discord_files(file_paths)
    except Exception as e:
        await interaction.followup.send(
            "Bilinmeyen bir hata oluştu, lütfen tekrar deneyin", ephemeral=True
        )
        raise e  # re-raise the exception so we can see what went wrong


async def download_video_command(
    interaction: discord.Interaction,
    url: str,
    is_ephemeral: bool = False,
    include_title: bool | None = None,
):
    url = get_url_from_text(url)
    url = _process_url(url)

    downloader = get_downloader(url)

    if downloader is None:
        logging.info("Found an unsupported link: %s", url)
        _ = await interaction.response.defer(ephemeral=True)
        return await try_unknown_link(interaction, url, include_title)

    _ = await interaction.response.defer(ephemeral=is_ephemeral)

    attachments = await get_details(downloader, url, interaction)
    if attachments is None:
        return

    discord_files = await _convert_to_discord_files(interaction, attachments)

    real_caption = (
        attachments.caption or f"Video{'s' if len(attachments) > 1 else ''} Downloaded"
    )
    caption, view = _get_caption_and_view(real_caption, include_title)
    caption = caption or discord.utils.MISSING

    await interaction.followup.send(
        caption, files=discord_files, ephemeral=is_ephemeral, view=view
    )


async def loading_animation(message: discord.WebhookMessage):
    original_text = message.content
    sleep_time = (
        0  # we don't actually need to sleep thanks to ``message.edit`` being async
    )
    while True:
        _ = await message.edit(content=original_text + ".", view=discord.ui.View())
        await asyncio.sleep(sleep_time)
        _ = await message.edit(content=original_text + "..", view=discord.ui.View())
        await asyncio.sleep(sleep_time)
        _ = await message.edit(content=original_text + "...", view=discord.ui.View())
        await asyncio.sleep(sleep_time)


async def try_unknown_link(
    interaction: discord.Interaction, url: str, include_title: bool | None = None
):
    """Edits the sent message if the download is successful, otherwise sends an error message.

    Args:
        interaction (discord.Interaction): the interaction to edit with ``interaction.response.edit_message``
        url (str): the url to download the video from
        include_title (bool | None, optional): whether to include the title in the caption. Defaults to None.
    """
    downloader = UnknownAlternateDownloader
    sent_message = await interaction.followup.send(
        "Bu link resmi olarak desteklenmiyor, yine de indirmeyi deniyorum",
        ephemeral=True,
        wait=True,
    )
    loading_task = asyncio.create_task(loading_animation(sent_message))

    try:
        attachments = await downloader.download_video_from_link(url)
        file_paths = [attachment.path for attachment in attachments]
        discord_files = _convert_paths_to_discord_files(file_paths)
    except Exception as e:
        _ = loading_task.cancel()
        _ = await sent_message.edit(content="Linki ne yazıkki indiremedim")
        raise e  # re-raise the exception so we can see what went wrong

    real_caption = (
        attachments.caption or f"Video{'s' if len(attachments) > 1 else ''} Downloaded"
    )
    caption, view = _get_caption_and_view(real_caption, include_title)
    caption = caption or ""

    _ = loading_task.cancel()
    _ = await sent_message.edit(content=f"{url} downloaded")
    await interaction.followup.send(content=caption, files=discord_files, view=view)
