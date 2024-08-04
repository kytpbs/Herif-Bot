import logging
import os
import bs4
from dotenv import load_dotenv
import requests

from src.downloader import VideoDownloader, VideoFile, VIDEO_RETURN_TYPE
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
    def download_video_from_link(
        url: str, path: str | None = None
    ) -> VIDEO_RETURN_TYPE:
        attachment_list: VIDEO_RETURN_TYPE = []
        try:
            response = requests.get(API_URL_START + url, timeout=30)
        except requests.exceptions.RequestException as e:
            logging.error("Error while downloading tweet: %s", str(e))
            return attachment_list
        data = bs4.BeautifulSoup(response.text, "html.parser")

        download_buttons: list[bs4.element.Tag] = data.find_all(
            "div", class_="origin-top-right"
        )

        for index, button in enumerate(download_buttons):
            highest_quality_url_button = button.find("a")

            if not isinstance(highest_quality_url_button, bs4.element.Tag):
                logging.warning("No highest quality url button found at index %d URL: %s", index, url)
                continue

            highest_quality_url = highest_quality_url_button.get(
                "href"
            )  # Highest quality video url button

            if not isinstance(highest_quality_url, str):
                logging.error("No highest quality url found at index %d URL: %s", index, url)
                continue

            tweet_id = get_tweet_id(url)

            # add index to filename to avoid overwriting
            if tweet_id is not None:
                filename = tweet_id + "_" + str(index)
            else:
                filename = (
                    get_filename_from_data(data) + "_" + str(index)
                )  # just in case both filenames are the same

            attachment = _download_video_from_link(
                highest_quality_url, filename=filename, path=path
            )

            if attachment is None:
                continue

            attachment_list.append(VideoFile(attachment))

        return attachment_list
