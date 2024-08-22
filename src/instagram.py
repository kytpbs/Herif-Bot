import asyncio
import logging
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from instaloader import ConnectionException, LoginException
from instaloader.instaloader import Instaloader
from instaloader.structures import Post
import requests
import yt_dlp

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

    username = os.getenv("INSTAGRAM_USERNAME")
    if username is None:
        logging.error("INSTAGRAM_USERNAME is not set in the environment variables")
        return False
    logging.debug("Logging in to instagram as %s", username)
    session_data = json_read("instagram_session", False)

    if session_data:
        downloader.load_session(username, session_data)
        return True

    if (session_data:=os.getenv("INSTAGRAM_SESSION")):
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
        write_json("instagram_session", session)
        return True
    except LoginException as e:
        logging.error("Instagram login failed!!! FIX CREDENTIALS. Error: %s", e)
        return False

def _try_login():
    global logged_in # pylint: disable=global-statement # don't really mind having a global login
    if not logged_in:
        logged_in = _login()
        logging.debug("Logged in to instagram" if logged_in else "Couldn't log into instagram")



_try_login()


def _get_shortcode_from_url(url: str) -> str | None:
    result = re.match(_SHORTCODE_REGEX, url)
    if result is None:
        return None
    shortcode = result.group(1)
    if not isinstance(shortcode, str):
        return None
    return shortcode

def _get_post_from_url(url: str) -> Post | None:
    shortcode = _get_shortcode_from_url(url)
    if shortcode is None:
        return None
    try:
        return Post.from_shortcode(downloader.context, shortcode)
    except ConnectionException as e:  # probably graphql error
        logging.exception(e)
        return None

def _get_file_name(post: Post, index: int) -> str:
    is_multi_vid = post.typename == "GraphSidecar"
    to_add = f"_{index}" if is_multi_vid else ""
    return f"{post.shortcode}{to_add}.mp4"

class InstagramAlternativeDownloader(VideoDownloader):
    @classmethod
    async def download_video_from_link(cls, url: str, path: str | None = None) -> VIDEO_RETURN_TYPE:
        attachment_list: VIDEO_RETURN_TYPE = []
        if path is None:
            path = os.path.join("downloads", "instagram")

        os.makedirs(path, exist_ok=True)

        cookies = json_read("instagram_session")

        specific_options = {
            'format': 'best',
            "outtmpl": os.path.join(path, "%(id)s.%(ext)s"),
            'noplaylist': True,
            'default_search': 'auto',
            'nooverwrites': True,
            'quiet': True,
        }

        # Download the video
        with yt_dlp.YoutubeDL(specific_options) as ydl:
            requests.utils.cookiejar_from_dict(cookies, ydl.cookiejar)
            ydt = await asyncio.to_thread(ydl.extract_info, url, download=True)

        if ydt is None:
            return []

        infos: list[dict] = ydt.get("entries", [ydt])
        # get the description as instagram posts don't have titles
        title = infos[0].get("description", None)
        for info in infos:
            video_id = info["id"]
            video_extension = info["ext"]
            if video_id is None:
                continue

            if video_extension != "mp4":
                logging.error("Got a non-mp4 file that is %s from this link: %s", video_extension, url)

            file_path = os.path.join(path, f"{video_id}.{video_extension}")

            attachment_list.append(VideoFile(file_path, title))
            title = None # only add the title to the first video

        return attachment_list


class InstagramDownloader(VideoDownloader):
    @classmethod
    async def download_video_from_link(cls, url: str, path: str | None = None) -> VIDEO_RETURN_TYPE:
        attachment_list: VIDEO_RETURN_TYPE = []
        _try_login() # try to login if not already logged in

        if path is None:
            path = os.path.join("downloads", "instagram")

        os.makedirs(path, exist_ok=True)

        post = _get_post_from_url(url)
        # if we can't get the post, use the alternative downloader
        if post is None:
            logging.warning("Couldn't get post from url: %s in instaloader, trying alternative downloader", url)
            return await InstagramAlternativeDownloader.download_video_from_link(url, path)

        downloader.filename_pattern = "{shortcode}"

        video_count = len(list(filter(None, post.get_is_videos())))

        downloaded: bool = False
        caption = post.caption
        for index in range(1, video_count + 1): # will run once if not sidecar
            file_path = os.path.join(path, _get_file_name(post, index))
            file = VideoFile(file_path, caption)
            caption = None

            if not os.path.exists(file.path) and not downloaded:
                await asyncio.to_thread(downloader.download_post, post, Path(path))
                downloaded = True

            attachment_list.append(file)

        return attachment_list
