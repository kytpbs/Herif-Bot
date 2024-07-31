import logging
import os
import bs4
from dotenv import load_dotenv
import requests

from src.downloader import VideoDownloader, VideoFile
from src.Helpers.twitter_helpers import get_filename_from_data, get_tweet_id

load_dotenv()
API_URL_START = "https://twitsave.com/info?url="


def _download_video_from_link(url: str, filename: int | str, path: str | None = None):
    """
    Downloads Videos from a twitter tweet,
    if path is None, the default path is downloads/twitter

    Args:
        filename (Tweet): the file name to save the video as
        path (str | None, optional): Path to download all the attachments to. Defaults to None.

    Returns:
        int : count of attachments downloaded
    """
    if path is None:
        path = os.path.join("downloads", "twitter")

    os.makedirs(path, exist_ok=True)

    try:
        response = requests.get(url, timeout=30)
    except requests.exceptions.RequestException as e:
        logging.error("Error while downloading tweet: %s", str(e))
        return None

    filepath = os.path.join(
        path,
        f"{filename}.mp4",
    )
    with open(
        filepath,
        "wb",
    ) as file:
        file.write(response.content)

    return filepath

class TwitterDownloader(VideoDownloader):
    @staticmethod
    def download_video_from_link(url: str, path: str | None = None) -> list[VideoFile]:
        attachment_list: list[VideoFile] = []
        try:
            response = requests.get(API_URL_START + url, timeout=30)
        except requests.exceptions.RequestException as e:
            logging.error("Error while downloading tweet: %s", str(e))
            return attachment_list
        data = bs4.BeautifulSoup(response.text, "html.parser")

        #TODO: ERROR-HANDLING: Try-Catch for the scraping going wrong
        download_button = data.find_all("div", class_="origin-top-right")[0]
        quality_buttons = download_button.find_all("a")
        highest_quality_url = quality_buttons[0].get("href")  # Highest quality video url

        tweet_id = get_tweet_id(url)
        filename = tweet_id if tweet_id is not None else get_filename_from_data(data)
        # TODO: Handle multiple attachments, currenly don't know what happens with multiple attachments
        attachment = _download_video_from_link(
            highest_quality_url, filename=filename, path=path
        )

        if attachment is None:
            return attachment_list

        attachment_list.append(VideoFile(attachment))

        return attachment_list
