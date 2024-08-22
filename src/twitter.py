import asyncio
import logging
import os
import re
import bs4
from dotenv import load_dotenv
import requests
import yt_dlp

from src.downloader import VideoDownloader, VideoFile, VIDEO_RETURN_TYPE


load_dotenv()
_TWITTER_ID_REGEX = r"status/(\d+)"
API_URL_START = "https://twitsave.com/info?url="


def _get_tweet_id(url: str) -> str | None:
    match = re.search(_TWITTER_ID_REGEX, url)
    return match.group(1) if match else None


def _get_highest_quality_url_list(response: requests.Response) -> list[str]:
    highest_quality_url_list: list[str] = []
    data = bs4.BeautifulSoup(response.text, "html.parser")
    url = response.url

    download_buttons: list[bs4.element.Tag] = data.find_all(
        "div", class_="origin-top-right"
    )

    for index, button in enumerate(download_buttons):
        highest_quality_url_button = button.find("a")

        if not isinstance(highest_quality_url_button, bs4.element.Tag):
            logging.warning(
                "No highest quality url button found at index %d in URL: %s", index, url
            )
            continue

        highest_quality_url = highest_quality_url_button.get(
            "href"
        )  # Highest quality video url button

        if not isinstance(highest_quality_url, str):
            logging.error(
                "No highest quality url found at index %d in URL: %s", index, url
            )
            continue

        highest_quality_url_list.append(highest_quality_url)

    return highest_quality_url_list


class TwitterAlternativeDownloader(VideoDownloader):
    @classmethod
    async def download_video_from_link(
        cls, url: str, path: str | None = None
    ) -> VIDEO_RETURN_TYPE:
        attachment_list: VIDEO_RETURN_TYPE = []

        if path is None:
            path = os.path.join("downloads", "twitter")

        os.makedirs(path, exist_ok=True)

        specific_options = {
            "format": "best",
            "outtmpl": os.path.join(path, "%(id)s.%(ext)s"),
            "noplaylist": True,
            "default_search": "auto",
            "nooverwrites": True,
            "quiet": True,
        }

        with yt_dlp.YoutubeDL(specific_options) as ydl:
            ydt = await asyncio.to_thread(ydl.extract_info, url, download=True)

        if ydt is None:
            return []

        infos: list[dict] = ydt.get("entries", [ydt])
        title = infos[0].get("title", None)
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
            title = None  # only add the title to the first video

        return attachment_list


class TwitterDownloader(VideoDownloader):
    @classmethod
    async def download_video_from_link(
        cls, url: str, path: str | None = None
    ) -> VIDEO_RETURN_TYPE:
        attachment_list: VIDEO_RETURN_TYPE = []
        tweet_id = _get_tweet_id(url)
        if path is None:
            path = os.path.join("downloads", "twitter")

        try:
            response = requests.get(API_URL_START + url, timeout=30)
        except requests.exceptions.RequestException as e:
            logging.warning(
                "Downloading from 3'rd party failed due to error: %s, trying with alternative downloader",
                e,
                exc_info=True,
            )
            return await TwitterAlternativeDownloader.download_video_from_link(
                url, path
            )

        if tweet_id is None:
            logging.error("No tweet id found in URL: %s", url)
            return attachment_list

        download_urls = _get_highest_quality_url_list(response)
        downloaded_file_paths = await cls._download_links(download_urls, path, tweet_id)

        attachment_list = [VideoFile(path) for path in downloaded_file_paths]

        return attachment_list
