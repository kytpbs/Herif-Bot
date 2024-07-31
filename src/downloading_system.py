import re
from typing import Type

from src.Youtube import YoutubeDownloader
from src.downloader import VideoDownloader
from src.twitter import TwitterDownloader

_TWITTER_REGEX = re.compile(r"\b(?:https?:\/\/)?(?:www\.)?(?:twitter\.com\/|t\.co\/|x\.com\/)\S*")
_INSTAGRAM_REGEX = re.compile(r"\b(?:https?:\/\/)?(?:www\.)?(?:instagram\.com\/|instagr\.am\/)\S*")
_YOUTUBE_REGEX = re.compile(r"\b(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/|youtu\.be\/)\S*")


def get_downloader(url: str) -> Type[VideoDownloader] | None:
    """
    Returns the correct downloader for the given url
    """
    if re.match(_TWITTER_REGEX, url):
        return TwitterDownloader
    if re.match(_YOUTUBE_REGEX, url):
        return YoutubeDownloader
    return None
