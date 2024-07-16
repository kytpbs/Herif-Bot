from asyncio import Lock
import logging
import os
import shutil

from discord import Attachment, File, HTTPException, Message, NotFound

deleted_messages_lock = Lock()


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
            try:
                logging.debug("Downloading attachment %s", attachment.url)
                await attachment.save(file_path, use_cached=True)  # type: ignore # the type is correct, but the library is not updated
            except (HTTPException, NotFound):
                logging.error("Couldn't download attachment %s", attachment.url)
                continue


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
        logging.info("Deleting saved attachments!")
        shutil.rmtree(
            os.path.join("downloads", "attachments"),
            ignore_errors=True,
            onerror=logging.error,
        )
        logging.debug("Deleted saved attachments")
