import asyncio
import logging
from abc import ABC, abstractmethod
import os
from typing import Any

import aiohttp
import requests
import yt_dlp

_NONE_STRING = "Doesn't exist"


class VideoFile:
    """
    Video object that contains the title, and its file path.
    """
    def __init__(self, file_path: str, title: str | None = None) -> None:
        self._title = title
        self._file_path = file_path

    def __str__(self) -> str:
        return f"Title: {self._title}, File Path: {self._file_path}"

    def __repr__(self) -> str:
        return f'Title: {self._title or _NONE_STRING}, File Path: {self._file_path or _NONE_STRING}'

    def __hash__(self) -> int:
        return hash((self._title, self._file_path))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VideoFile):
            return False
        return self._title == other._title and self._file_path == other._file_path

    @property
    def caption(self) -> str | None:
        return self._title

    @property
    def path(self) -> str:
        return self._file_path



VIDEO_RETURN_TYPE = list[VideoFile]

class VideoDownloader(ABC):
    """
    INTERPHASE FOR DOWNLOADING CONTENT FROM A WEBSITE
    """

    @classmethod
    @abstractmethod
    async def download_video_from_link(cls, url: str, path: str | None = None) -> VIDEO_RETURN_TYPE:
        """
        Downloads Videos from a url
        if path is None, the default path is downloads/{website_name}

        if the download fails, it returns an empty list
        """
        logging.error(
            "VideoDownloader download_url interface was directly called, this should not happen! url was: %s for path: %s",
            url,
            path,
        )
        return []

    @classmethod
    async def _download_link(cls, url: str, download_to: str) -> str | None:
        """
        Downloads a file from the given URL and saves it to the specified path.
        
        
        Warning:
            This function will not overwrite existing files. If the file already exists at the specified path, it will not be downloaded again.

        Args:
            url (str): The URL of the file to download.
            download_to (str): The local file path where the downloaded file should be saved.

        Returns:
            downloaded_path (str): The path to the downloaded file if successful, otherwise None.
        """
        # if we already downloaded the file before, return it
        if os.path.exists(download_to):
            return download_to

        os.makedirs(os.path.dirname(download_to), exist_ok=True)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.read()
                    with open(download_to, "wb") as file:
                        file.write(data)
        except aiohttp.ClientError as e:
            logging.error("Error while downloading instagram post: %s", str(e))
            return None
        return download_to

    @classmethod
    async def _download_links(cls, links: list[str], path: str, video_id: str) -> list[str]:
        """Downloads files from a list of URLs and saves them to the specified path.
        Will not overwrite existing files. If a file already exists at the specified path, it will not be downloaded again.
        Adds _{index} to the filename to avoid overwriting files with the same name.

        Args:
            links (list[str]): the list of URLs to download, will add _{index} starting at 1 to the filename for every file
            path (str): the local file path where the downloaded files should be saved
            video_id (str): the video ID to use in the filename, is the same thing as filename

        Returns:
            list[str]: the list of paths to the downloaded files
            will not put the path in the list if the download failed
        """
        downloaded_paths = []
        for index, link in enumerate(links, start=1):
            download_to = os.path.join(path, f"{video_id}_{index}.mp4")
            downloaded_link = await cls._download_link(link, download_to)
            if downloaded_link is None:
                continue
            downloaded_paths.append(downloaded_link)

        return downloaded_paths

class AlternateVideoDownloader(VideoDownloader):
    @classmethod
    async def _get_list_from_ydt(cls, url: str, ydl_opts: dict[str, Any], path: str, title_key: str = "title", cookies: dict | None = None) -> VIDEO_RETURN_TYPE:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if cookies:
                requests.utils.cookiejar_from_dict(cookies, ydl.cookiejar)    
            try:
                ydt = await asyncio.to_thread(ydl.extract_info, url, download=True)
            except yt_dlp.DownloadError as e:
                logging.error("Couldn't download video from url: %s, Error: %s", url, e, exc_info=True)
                return []

        if ydt is None:
            return []

        infos: list[dict[str, Any]] = ydt.get("entries", [ydt])

        attachment_list: VIDEO_RETURN_TYPE = []
        title = infos[0].get(title_key, None)
        url = infos[0].get("webpage_url", "URL-NOT-FOUND")
        for info in infos:
            video_id = info["id"]
            video_extension = info["ext"]
            if video_id is None:
                continue

            if video_extension != "mp4":
                logging.error(
                    "Got a non-mp4 file that is %s from this link: %s",
                    video_extension,
                    url,
                )

            file_path = os.path.join(path, f"{video_id}.{video_extension}")

            attachment_list.append(VideoFile(file_path, title))
            # only add the title to the first video, or else we duplicate the title for each video
            title = None

        return attachment_list
