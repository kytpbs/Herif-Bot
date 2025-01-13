import os
import threading

import yt_dlp
from src.voice.music_base import Music

DOWNLOAD_FOLDER = os.path.join("downloads", "youtube_mp3")


_to_download: list[str] = []
_downloaded: list[str] = []
_errored_out: list[str] = []


def _hook(progress: dict):
    status = progress["status"]
    if status != "downloading":
        video_id = progress["info_dict"]["id"]
        _to_download.remove(video_id)
        # the rest is temporary, delete, as the lists will become too big after a while
        if status == "finished":
            _downloaded.append(video_id)
        else:
            _errored_out.append(video_id)


ydl_opts = {
    "progress_hooks": [_hook],
    "format": "bestaudio",
    "noplaylist": True,
    "default_search": "auto",
    "keepvideo": False,
    "nooverwrites": True,
    "quiet": True,
    "outtmpl": "downloads/youtube_mp3/%(id)s.mp3",
}


def _actually_download_video(link: str):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(link, download=True)


def start_downloading(music: Music):
    if os.path.exists(get_download_path(music)):
        _downloaded.append(music.id)
        return

    _to_download.append(music.id)
    threading.Thread(
        target=_actually_download_video,
        args=[music.url],
        name=f"{music.title} downloader",
    ).start()


def is_downloaded(music: Music):
    return music.id in _downloaded


def is_errored_out(music: Music):
    return music.id in _errored_out


def get_download_path(music: Music):
    return os.path.join(DOWNLOAD_FOLDER, f"{music.id}.mp3")
