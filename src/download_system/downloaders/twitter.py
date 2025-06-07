import logging
import os
import re
import bs4
from dotenv import load_dotenv
import requests

from src.download_system.downloader import (
    AlternateVideoDownloader,
    DownloadFailedError,
    VideoDownloader,
    VideoFile,
    VIDEO_RETURN_TYPE,
    VideoFiles,
)


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

    download_buttons = data.find_all("div", class_="origin-top-right")

    for index, button in enumerate(download_buttons):
        if not isinstance(button, bs4.element.Tag):
            logging.warning(
                "Download button at index %d is not a Tag element in URL: %s",
                index,
                url,
            )
            continue

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


def _get_title(response: requests.Response) -> str:
    data = bs4.BeautifulSoup(response.text, "html.parser")
    title = data.find("p", class_="m-2")

    if not isinstance(title, bs4.element.Tag):
        logging.warning("No title found in URL: %s", response.url)
        return "No title found"

    return title.text


class TwitterAlternativeDownloader(AlternateVideoDownloader):
    @classmethod
    async def download_video_from_link(
        cls, url: str, path: str | None = None
    ) -> VIDEO_RETURN_TYPE:
        if path is None:
            path = os.path.join("downloads", "twitter")

        os.makedirs(path, exist_ok=True)

        specific_options = {
            "format": "best",  # for some reason twitter downloading in yt-dlp does not work with the same format as youtube
            "outtmpl": os.path.join(path, "%(id)s.%(ext)s"),
            "noplaylist": True,
            "default_search": "auto",
            "nooverwrites": True,
            "quiet": True,
        }

        return await cls._get_list_from_ydt(url, specific_options, path)


class TwitterDownloader(VideoDownloader):
    @classmethod
    async def download_video_from_link(
        cls, url: str, path: str | None = None
    ) -> VIDEO_RETURN_TYPE:
        attachment_list: list[VideoFile] = []
        tweet_id = _get_tweet_id(url)
        if path is None:
            path = os.path.join("downloads", "twitter")

        try:
            response = requests.get(API_URL_START + url, timeout=30)
            response.raise_for_status()
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
            raise DownloadFailedError(f"No tweet id found in URL: {url}")

        download_urls = _get_highest_quality_url_list(response)
        title = _get_title(response)
        downloaded_file_paths = await cls._download_links(download_urls, path, tweet_id)

        attachment_list = [VideoFile(path) for path in downloaded_file_paths]

        if not attachment_list:
            logging.error(
                "No video was downloaded for this link, trying alternate downloader",
                exc_info=True,
            )
            return await TwitterAlternativeDownloader.download_video_from_link(
                url, path
            )

        return VideoFiles(attachment_list, title)
