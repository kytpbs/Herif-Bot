import asyncio
import logging
from typing import Optional, Type
import discord

from src.downloader import (
    VIDEO_RETURN_TYPE,
    AbstractClassUsedError,
    DownloadFailedError,
    NoVideoFoundError,
    VideoDownloader,
)
from src.other import UnknownAlternateDownloader
from src.downloading_system import get_downloader, get_url_from_text


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
    caption = caption.split("\n")[0]

    punctuation_index = _get_shortest_punctuation_index(caption)
    if punctuation_index:
        return caption[: punctuation_index + 1]
    return caption[:100]


def _get_view(shortened_caption: str, caption: str):
    view = discord.ui.View()
    button = discord.ui.Button(label="🔽\nExpand", style=discord.ButtonStyle.secondary)

    async def callback(interaction: discord.Interaction):
        revert_view = discord.ui.View()
        button = discord.ui.Button(
            label="🔼\nShorten", style=discord.ButtonStyle.secondary
        )

        async def callback(interaction: discord.Interaction):
            await interaction.response.edit_message(
                content=shortened_caption, view=view
            )

        button.callback = callback
        revert_view.add_item(button)
        await interaction.response.edit_message(content=caption, view=revert_view)

    button.callback = callback
    view.add_item(button)
    return view


def _get_caption_and_view(
    real_caption: str, include_title: Optional[bool]
) -> tuple[Optional[str], discord.ui.View]:
    shortened_caption = _get_shortened_caption(real_caption) + " ***...***"
    view = discord.utils.MISSING

    if include_title is False:
        caption = None

    elif include_title is True:
        caption = real_caption

    elif len(shortened_caption) < len(real_caption):
        view = _get_view(shortened_caption, real_caption)
        caption = shortened_caption
    else:
        caption = real_caption

    return caption, view


async def get_details(
    downloader: Type[VideoDownloader], url: str, interaction: discord.Interaction
) -> Optional[VIDEO_RETURN_TYPE]:
    try:
        return await downloader.download_video_from_link(url)
    except DownloadFailedError:
        await interaction.followup.send(
            "Failed to download the video, error saved, please try again later",
            ephemeral=True,
        )
        logging.exception("Failed Downloading Link: %s", url, exc_info=True)
        return
    except NoVideoFoundError:
        await interaction.followup.send(
            "Couldn't find a video on the page, are you sure this is a **video** link?",
            ephemeral=True,
        )
        logging.exception("Couldn't find link on url %s", url, exc_info=True)
        return
    except AbstractClassUsedError:
        await interaction.followup.send(
            "Something went horribly wrong, error saved, please try again later", 
            ephemeral=True
        )
        logging.exception(
            "An abstract class was used, this should not happen", exc_info=True
        )
        return
    except Exception as e:
        await interaction.followup.send(
            "An unknown error occurred, report saved, please try again later", 
            ephemeral=True
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
            "An unknown error occurred, error saved, please report if not fixed after a while", ephemeral=True
        )
        raise e  # re-raise the exception so we can see what went wrong


async def download_video_command(
    interaction: discord.Interaction,
    url: str,
    is_ephemeral: bool = False,
    include_title: bool | None = None,
):
    url = get_url_from_text(url)

    downloader = get_downloader(url)

    if downloader is None:
        logging.info("Found an unsupported link: %s", url)
        await interaction.response.defer(ephemeral=True)
        return await try_unknown_link(interaction, url, include_title)

    await interaction.response.defer(ephemeral=is_ephemeral)

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
        await message.edit(content=original_text + ".", view=discord.ui.View())
        await asyncio.sleep(sleep_time)
        await message.edit(content=original_text + "..", view=discord.ui.View())
        await asyncio.sleep(sleep_time)
        await message.edit(content=original_text + "...", view=discord.ui.View())
        await asyncio.sleep(sleep_time)


async def try_unknown_link(
    interaction: discord.Interaction, url: str, include_title: Optional[bool] = None
):
    """edits the sent message if the download is successful, otherwise sends an error message

    Args:
        interaction (discord.Interaction): the interaction to edit with ``interaction.response.edit_message``
        url (str): the url to download the video from
    """

    downloader = UnknownAlternateDownloader
    sent_message = await interaction.followup.send(
        "This link is not supported, attempting to download anyway",
        ephemeral=True,
        wait=True,
    )
    loading_task = asyncio.create_task(loading_animation(sent_message))

    try:
        attachments = await downloader.download_video_from_link(url)
        file_paths = [attachment.path for attachment in attachments]
        discord_files = _convert_paths_to_discord_files(file_paths)
    except Exception as e:
        loading_task.cancel()
        await sent_message.edit(content="Sorry, failed to download the video(s)")
        raise e  # re-raise the exception so we can see what went wrong

    real_caption = (
        attachments.caption or f"Video{'s' if len(attachments) > 1 else ''} Downloaded"
    )
    caption, view = _get_caption_and_view(real_caption, include_title)
    caption = caption or ""

    loading_task.cancel()
    await sent_message.edit(content=f"{url} downloaded" if not include_title else "")
    await interaction.followup.send(content=caption, files=discord_files, view=view)
