import logging
import shutil
from asyncio import Lock
from pathlib import Path

import requests
from discord import Attachment, File, Message

from Constants import ATTACHMENT_DOWNLOAD_PATH

deleted_messages_lock = Lock()
logger = logging.getLogger("file_handeler")


def get_deleted_messages_lock():
    return deleted_messages_lock


def _get_file_path_of_attachment(attachment: Attachment) -> Path:
    """Returns the path to the file of the attachment.

    WARNING: This function does not check if the file exists. and returns the expected path.
    """
    return ATTACHMENT_DOWNLOAD_PATH / (
        str(attachment.id) + "." + attachment.filename.split(".")[-1]
    )


async def download_all_attachments(message: Message):
    async with deleted_messages_lock:
        for attachment in message.attachments:
            file_path = _get_file_path_of_attachment(attachment)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            _download_file(attachment.url, file_path)


def _download_file(url: str, file_path: Path):
    try:
        logger.debug("Downloading file %s", url)
        response = requests.get(url, timeout=30)  # download the file

        content = response.content
        if not file_path.parent.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)

        if response.status_code != 200:
            logger.error(
                "Got status code %d while trying to download %s",
                response.status_code,
                url,
            )
            return

        with file_path.open("wb") as file:
            file.write(content)
    except requests.RequestException as e:
        logger.exception("Couldn't download file %s got error: %s", url, e)


def get_deleted_attachment(attachment: Attachment) -> File | None:
    file_path = _get_file_path_of_attachment(attachment)
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
