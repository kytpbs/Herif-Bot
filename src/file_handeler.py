from asyncio import Lock
import logging
import os
from pathlib import Path
import shutil

import discord

deleted_messages_lock = Lock()
logger = logging.getLogger("file_handeler")


def get_deleted_messages_lock():
    return deleted_messages_lock


def _get_file_path_of_attachment(attachment: discord.Attachment) -> str:
    """
    Returns the path to the file of the attachment.
    WARNING: This function does not check if the file exists. and returns the expected path.
    """
    return os.path.join(
        "downloads",
        "attachments",
        str(attachment.id) + "." + attachment.filename.split(".")[-1],
    )


async def download_all_attachments(message: discord.Message):
    os.makedirs(os.path.join("downloads", "attachments"), exist_ok=True)
    async with deleted_messages_lock:
        for attachment in message.attachments:
            file_path = Path(_get_file_path_of_attachment(attachment))
            await _download_file(attachment, file_path)


async def _download_file(attachment: discord.Attachment, file_path: os.PathLike[str]):
    error: Exception | None = None
    # Maybe use aiofiles here? since discord.py seems to be using sync file operations
    try:
        logger.debug(
            "Downloading file '%s' at url '%s'", attachment.filename, attachment.url
        )
        _ = await attachment.save(file_path)
        return
    except discord.NotFound:
        # This probably would never happen since we are downloading it the moment it is sent
        try:
            logger.debug(
                "Downloading file '%s' at url '%s'",
                attachment.filename,
                attachment.proxy_url,
            )
            _ = await attachment.save(file_path, use_cached=True)
            return
        except (discord.NotFound, discord.HTTPException) as e:
            error = e
    except discord.HTTPException as e:
        error = e
    logger.error("Couldn't download file %s got error: %s", attachment.url, error)


def get_deleted_attachment(attachment: discord.Attachment) -> discord.File | None:
    file_path = _get_file_path_of_attachment(attachment)
    if os.path.exists(file_path):
        return discord.File(
            file_path,
            filename=attachment.filename,
            spoiler=attachment.is_spoiler(),
        )
    return None


async def delete_saved_attachments():
    async with deleted_messages_lock:
        logger.info("Deleting saved attachments!")
        shutil.rmtree(
            os.path.join("downloads", "attachments"),
            ignore_errors=True,
            onerror=logger.error,
        )
        logger.debug("Deleted saved attachments")


def get_file_path_of_video(video_id: str) -> str:
    return os.path.join("downloads", "youtube", video_id + ".mp3")
