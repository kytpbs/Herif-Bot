import functools
import logging
import os
from queue import LifoQueue

import yt_dlp

from Constants import MAX_VIDEO_DOWNLOAD_SIZE
from src.downloader import VIDEO_RETURN_TYPE, VideoDownloader, VideoFile

ydl_opts = {
  'format': 'bestaudio',
  'noplaylist': True,
  'default_search': 'auto',
  'keepvideo': False,
  'nooverwrites': False,
  'quiet': True,
}


class video_data(object):

    def __init__(self, title=None, image_url=None, webpage_url=None, yt_dlp_dict=None):
        if image_url is not None:
            self.thumbnail_url = image_url
        else:
            self.thumbnail_url = None

        self.webpage_url = webpage_url

        if title is not None:
            self.title = title
        else:
            self.title = None

        if yt_dlp_dict is not None:
            video_info:dict = yt_dlp_dict['entries'][0]
            self.title = video_info['title']
            self.thumbnail_url = video_info['thumbnail']
            self.webpage_url = video_info.get('webpage_url', None)

    def has_data(self) -> bool:
        if (self.thumbnail_url is None) and (self.title is None) and (self.webpage_url is None):
            return False
        return True

    def set_title(self, title: str) -> None:
        self.title = title

    def set_thumbnail_url(self, thumbnail_url: str) -> None:
        self.thumbnail_url = thumbnail_url

    def set_webpage_url(self, webpage_url: str) -> None:
        self.webpage_url = webpage_url
        
    def set_yt_dlp_dict(self, yt_dlp_dict: dict) -> None:
        video_info = yt_dlp_dict['entries'][0]
        self.title = video_info['title']
        self.thumbnail_url = video_info['thumbnail']

    def __hash__(self) -> int:
        return hash((self.title, self.thumbnail_url, self.webpage_url))

class video_data_guild:
    def __init__(self) -> None:
        self.video_dict: dict[int, video_data] = {}

    def set_video_data(self, guild_id: int, video_data_instance: video_data) -> None:
        self.video_dict[guild_id] = video_data_instance

    def get_video_data(self, guild_id: int) -> video_data:
        return self.video_dict.get(guild_id, video_data())


def yt_dlp_hook(progress_queue: LifoQueue, download):
    progress_queue.put(download)


def youtube_download(video_url, progress_queue: LifoQueue, file_path_with_name):
    logging.debug(f"Downloading {video_url} to {file_path_with_name}")
    yt_dlp_hook_partial = functools.partial(yt_dlp_hook, progress_queue)
    ydl_opts_new = ydl_opts.copy()
    ydl_opts_new["outtmpl"] = file_path_with_name
    ydl_opts_new["progress_hooks"] = [yt_dlp_hook_partial]

    with yt_dlp.YoutubeDL(ydl_opts_new) as ydl:
        return ydl.download(url_list=[video_url])


last_played = video_data_guild()


def get_last_played_guilded() -> video_data_guild:
    return last_played

class YoutubeDownloader(VideoDownloader):
    @staticmethod
    def download_video_from_link(url: str, path: str | None = None) -> VIDEO_RETURN_TYPE:
        if path is None:
            path = os.path.join("downloads", "youtube")

        os.makedirs(path, exist_ok=True)

        costum_options = {
            'format': f'bestvideo[filesize<{MAX_VIDEO_DOWNLOAD_SIZE}M,ext=mp4]+bestaudio/best[filesize<{MAX_VIDEO_DOWNLOAD_SIZE}M,ext=mp4]]',
            "outtmpl": os.path.join(path, "%(id)s.mp4"),
            'noplaylist': True,
            'default_search': 'auto',
            'nooverwrites': True,
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(costum_options) as ydl:
            ydt = ydl.extract_info(url, download=True)

        if ydt is None:
            return []

        info = ydt.get("entries", [None])[0] or ydt
        video_id = info["id"]
        if video_id is None:
            return []

        file_path = os.path.join(path, f"{video_id}.mp4")

        return [VideoFile(file_path, info.get("title", None))]
