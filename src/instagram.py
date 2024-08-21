import logging
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from instaloader import ConnectionException, LoginException
from instaloader.instaloader import Instaloader
from instaloader.structures import Post

from Constants import JSON_FOLDER
from src.downloader import VIDEO_RETURN_TYPE, VideoFile, VideoDownloader
from src.Read import json_read, write_json

_SHORTCODE_REGEX = (
    r"^https?:\/\/(?:www\.)?instagram\.com\/[^\/]+(?:\/[^\/]+)?\/([^\/]{11})\/.*$"
)

load_dotenv()

logged_in = False

downloader = Instaloader(
    download_videos=True,
    download_pictures=False,
    save_metadata=False,
    download_comments=False,
)


def _login() -> bool:
    """
    Loads the session from the json file. or logs in if it doesn't exist.
    Safe to call multiple times.

    Returns:
        bool: True if the session was loaded successfully
    """
    if logged_in:
        return True

    session_path = os.path.join(JSON_FOLDER, "instagram_session.json")
    username = os.getenv("INSTAGRAM_USERNAME")
    if username is None:
        logging.error("INSTAGRAM_USERNAME is not set in the environment variables")
        return False
    if os.path.exists(session_path):
        session_data = json_read(session_path)

        downloader.load_session(username, session_data)
        return True

    if (session_data:=os.getenv("INSTAGRAM_SESSION")) is not None:
        # this function will only be used in github actions
        # so we can assume that the session data is in the correct format
        # and if not, it should crash anyways
        import json # pylint: disable=import-outside-toplevel # this is only used in this branch
        downloader.load_session(username, json.loads(session_data))
        return True


    password = os.getenv("INSTAGRAM_PASSWORD")
    if password is None:
        logging.error(
            "INSTAGRAM_PASSWORD was not set in the environment variables"
            + " and couldn't find instagram_session file in jsons folder"
        )
        return False
    try:
        downloader.login(username, password)
        session = downloader.save_session()
        write_json(session_path, session)
        return True
    except LoginException as e:
        logging.error("Instagram login failed!!! FIX CREDENTIALS. Error: %s", e)
        return False


logged_in = _login()


def _get_post_from_url(url: str) -> Post | None:
    result = re.match(_SHORTCODE_REGEX, url)
    if result is None:
        return None
    shortcode = result.group(1)
    if not isinstance(shortcode, str):
        return None
    try:
        return Post.from_shortcode(downloader.context, shortcode)
    except ConnectionException as e:  # probably graphql error
        logging.exception(e)
        return None


class InstagramDownloader(VideoDownloader):
    @staticmethod
    def download_video_from_link(url: str, path: str | None = None) -> VIDEO_RETURN_TYPE:
        attachment_list: VIDEO_RETURN_TYPE = []
        global logged_in  # pylint: disable=global-statement # can't think of a better way rn
        logged_in = _login()  # retry login if it failed the first time

        if path is None:
            path = os.path.join("downloads", "instagram")

        os.makedirs(path, exist_ok=True)

        path = Path(path)  # type: ignore

        post = _get_post_from_url(url)
        if post is None:
            return attachment_list
        downloader.filename_pattern = "{shortcode}"

        is_video_list = post.get_is_videos()
        is_video_list = list(filter(lambda x: x is True, is_video_list))

        downloaded: bool = False
        if post.typename == "GraphSidecar":
            for index, _ in enumerate(is_video_list, start=1):

                file_path = os.path.join(path, f"{post.shortcode}_{index}.mp4")  # type: ignore # there is a bug in pylance...
                file = VideoFile(file_path, post.caption)

                if not os.path.exists(file.path) and not downloaded:
                    downloader.download_post(post, path)  # type: ignore # path is literally a Path object it cannot be None...
                    downloaded = True

                attachment_list.append(file)
        else:
            file_path = os.path.join(path, f"{post.shortcode}.mp4") # type: ignore # there is a bug in pylance...
            file = VideoFile(file_path, post.caption)
            if not os.path.exists(file.path) and not downloaded:
                downloader.download_post(post, path) # type: ignore # path is literally a Path object it cannot be None...
                downloaded = True
            attachment_list.append(file)

        return attachment_list
