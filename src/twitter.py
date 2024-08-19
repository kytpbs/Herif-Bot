import logging
import os
import re
import bs4
from dotenv import load_dotenv
import requests

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
            logging.warning("No highest quality url button found at index %d in URL: %s", index, url)
            continue

        highest_quality_url = highest_quality_url_button.get(
            "href"
        )  # Highest quality video url button

        if not isinstance(highest_quality_url, str):
            logging.error("No highest quality url found at index %d in URL: %s", index, url)
            continue

        highest_quality_url_list.append(highest_quality_url)    

    return highest_quality_url_list

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
            logging.error("Error while downloading tweet: %s", str(e))
            return attachment_list

        if tweet_id is None:
            logging.error("No tweet id found in URL: %s", url)
            return attachment_list

        download_urls = _get_highest_quality_url_list(response)
        downloaded_file_paths = await cls._download_links(download_urls, path, tweet_id)

        attachment_list =  [VideoFile(path) for path in downloaded_file_paths]

        return attachment_list
