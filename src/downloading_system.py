import re
from typing import Type

from src.Youtube import YoutubeDownloader
from src.downloader import VideoDownloader
from src.instagram import InstagramDownloader
from src.twitter import TwitterDownloader

_URL_PARSE_REGEX = re.compile(r"\b((?:https?://)?(?:(?:www\.)?(?:[\da-z\.-]+)\.(?:[a-z]{2,6})|(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])))(?::[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])?(?:/[\w\.-]*)*/?)\b") # NOSONAR

_TWITTER_REGEX = re.compile(r"\b(?:https?:\/\/)?(?:www\.)?(?:twitter\.com\/|t\.co\/|x\.com\/)\S*")
_INSTAGRAM_REGEX = re.compile(r"\b(?:https?:\/\/)?(?:www\.)?(?:instagram\.com\/|instagr\.am\/)\S*")
_YOUTUBE_REGEX = re.compile(r"\b(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/|youtu\.be\/)\S*")


def get_downloader(url: str) -> Type[VideoDownloader] | None:
    """
    Returns the correct downloader for the given url if it can't find it
    it tries to extract the url incase there is extra text in the url string
    if it still can't find a downloader, it returns None
    """

    if re.match(_TWITTER_REGEX, url):
        return TwitterDownloader
    if re.match(_INSTAGRAM_REGEX, url):
        return InstagramDownloader
    if re.match(_YOUTUBE_REGEX, url):
        return YoutubeDownloader
    # try to extract the url from the text incase there is extra text
    if (result := re.search(_URL_PARSE_REGEX, url)) and result.group(0) != url:
        return get_downloader(result.group(0))
    return None
