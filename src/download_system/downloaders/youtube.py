import logging
import os

import requests

from Constants import MAX_VIDEO_DOWNLOAD_SIZE
from src.download_system.downloader import VIDEO_RETURN_TYPE, AlternateVideoDownloader, VideoFile, VideoFiles

_API_URL = "https://api.cobalt.tools/"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.67",
    "accept": "application/json",
    "accept-language": "tr,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,de-DE;q=0.6,de;q=0.5",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Microsoft Edge\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "Referer": "https://cobalt.tools/",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}


class YoutubeDownloader(AlternateVideoDownloader):
    @classmethod
    async def download_video_from_link(cls, url: str, path: str | None = None) -> VIDEO_RETURN_TYPE:
        if path is None:
            path = os.path.join("downloads", "youtube")

        try:
            response = requests.post(_API_URL, json={"url": url}, headers=_HEADERS, timeout=15)
            response.raise_for_status()
            data: dict = response.json()
        except requests.exceptions.RequestException as e:
            logging.error("Downloading from 3'rd party failed due to error: %s", e, exc_info=True)
            return await AlternateYoutubeDownloader.download_video_from_link(url, path)

        if not (download_link:=data.get("url")):
            logging.error("No download link found in response: %s", data)
            return await AlternateYoutubeDownloader.download_video_from_link(url, path)

        downloaded_file_paths = await cls._download_links([download_link], path, data.get("filename", "unknown_temp"))

        attachment_list = [VideoFile(path) for path in downloaded_file_paths]

        return VideoFiles(attachment_list, data.get("filename", "unknown_temp"))


class AlternateYoutubeDownloader(AlternateVideoDownloader):
    @classmethod
    async def download_video_from_link(cls, url: str, path: str | None = None) -> VIDEO_RETURN_TYPE:
        if path is None:
            path = os.path.join("downloads", "youtube")

        os.makedirs(path, exist_ok=True)

        costum_options = {
            # Exclude AV1 codec videos, prioritize H.264/H.265 encoded videos
            'format': f'bestvideo[filesize<{MAX_VIDEO_DOWNLOAD_SIZE}M][ext=mp4][vcodec!^=av01]+bestaudio[ext=m4a]/best[filesize<{MAX_VIDEO_DOWNLOAD_SIZE}M][ext=mp4][vcodec!^=av01]',
            "outtmpl": os.path.join(path, "%(id)s.mp4"),
            'noplaylist': True,
            'default_search': 'auto',
            'nooverwrites': True,
            'quiet': True,
        }

        return await cls._get_list_from_ydt(url, costum_options, path)
