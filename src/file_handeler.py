import asyncio
import logging
import shutil
from asyncio import Lock
from pathlib import Path

import aiohttp
import aiohttp.web
import anyio
from discord import Attachment, File, Message

from Constants import ATTACHMENT_DOWNLOAD_PATH

deleted_messages_lock = Lock()
logger = logging.getLogger("file_handeler")


def get_deleted_messages_lock():
    return deleted_messages_lock


def _get_file_path_for_attachment(attachment: Attachment) -> Path:
    """Returns the path to the file of the attachment.

    WARNING: This function does not check if the file exists. and returns the expected path.
    """
    return ATTACHMENT_DOWNLOAD_PATH / (
        str(attachment.id) + "." + attachment.filename.split(".")[-1]
    )


async def download_all_attachments(message: Message):
    async with get_deleted_messages_lock():
        _ = await asyncio.gather(
            *[
                _download_file(
                    attachment.url, _get_file_path_for_attachment(attachment)
                )
                for attachment in message.attachments
            ]
        )


async def _download_file(url: str, file_path: Path):
    try:
        logger.debug("Downloading file %s", url)
        async with (
            aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(15)) as session,
            session.get(url) as response,
        ):
            if response.status != aiohttp.web.HTTPOk.status_code:
                logger.error(
                    "Got status code %d while trying to download %s",
                    response.status,
                    url,
                )
                return
            content = await response.read()

        file_path.parent.mkdir(parents=True, exist_ok=True)

        async with await anyio.open_file(file_path, "wb") as file:
            _ = await file.write(content)

    except (aiohttp.ClientError, TimeoutError) as e:
        logger.exception("Couldn't download file %s got error: %s", url, e)


async def get_deleted_attachment(attachment: Attachment) -> File | None:
    async with get_deleted_messages_lock():
        file_path = _get_file_path_for_attachment(attachment)
        if file_path.exists():
            return File(
                file_path,
                filename=attachment.filename,
                spoiler=attachment.is_spoiler(),
            )
        return None


async def delete_saved_attachments():
    async with deleted_messages_lock:
        logger.info("Deleting saved attachments!")
        shutil.rmtree(
            ATTACHMENT_DOWNLOAD_PATH,
            ignore_errors=True,
            onerror=logger.error,
        )
        logger.debug("Deleted saved attachments")
