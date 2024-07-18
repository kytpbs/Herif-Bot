from asyncio import Lock
import logging
import os
import shutil

from discord import Attachment, File, Message
import requests

deleted_messages_lock = Lock()
logger = logging.getLogger("file_handeler")


def get_deleted_messages_lock():
    return deleted_messages_lock

def _get_file_path_of_attachment(attachment: Attachment) -> str:
    """
    Returns the path to the file of the attachment.
    WARNING: This function does not check if the file exists. and returns the expected path.
    """
    return os.path.join("downloads", "attachments", str(attachment.id) + "." + attachment.filename.split(".")[-1])

async def download_all_attachments(message: Message):
    os.makedirs(os.path.join("downloads", "attachments"), exist_ok=True)
    async with deleted_messages_lock:
        for attachment in message.attachments:
            file_path = _get_file_path_of_attachment(attachment)
            _download_file(attachment.url, file_path)


def _download_file(url: str, file_path: str):
    try:
        logger.debug("Downloading file %s", url)
        response = requests.get(url, timeout=30) # download the file

        content = response.content

        if response.status_code != 200:
            logger.error("Got status code %d while trying to download %s", response.status_code, url)
            return

        if not isinstance(content, bytes):
            logger.error("Didn't get bytes while trying to download file %s", url)
            return

        with open(file_path, "wb") as file:
            file.write(content)
    except (requests.RequestException) as e:
        logger.exception("Couldn't download file %s got error: %s", url, e)

def get_deleted_attachment(attachment: Attachment) -> File | None:
    file_path = _get_file_path_of_attachment(attachment)
    if os.path.exists(file_path):
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
            os.path.join("downloads", "attachments"),
            ignore_errors=True,
            onerror=logger.error,
        )
        logger.debug("Deleted saved attachments")

def get_file_path_of_video(video_id: str) -> str:
    return os.path.join("downloads", "youtube", video_id + ".mp3")
