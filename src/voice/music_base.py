import asyncio
import functools
import logging
from async_lru import alru_cache
import yt_dlp

ydl_opts = {
    "format": "bestaudio",
    "noplaylist": True,
    "default_search": "auto",
    "keepvideo": False,
    "nooverwrites": True,
    "quiet": True,
    "outtmpl": "downloads/youtube_mp3/%(id)s.mp3",
}

class MusicNotFoundError(Exception):
    pass

def _return_none_on_error_wrapper(func):
    @functools.wraps(func)
    async def wrapped(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except MusicNotFoundError as e:
            logging.debug("Music not found", exc_info=e)
            return None

    return wrapped


class Music:
    def __init__(self, music_id: str, title: str, thumbnail_url: str) -> None:
        from src.voice.download_manager import start_downloading # pylint: disable=import-outside-toplevel # circular import
        self.id = music_id
        self.title = title
        self.thumbnail_url = thumbnail_url

        start_downloading(self)

    def is_downloaded(self):
        from src.voice.download_manager import is_downloaded # pylint: disable=import-outside-toplevel # circular import
        return is_downloaded(self)

    def __hash__(self) -> int:
        return hash(self.id)

    @property
    def url(self):
        return f"https://www.youtube.com/watch?v={self.id}"

    @classmethod
    def from_yt_dlp(cls, yt_dlp_dict):
        video_info = yt_dlp_dict["entries"][0]
        return cls(video_info["id"], video_info["title"], video_info["thumbnail"])

    @classmethod
    def from_info_dict(cls, video_info):
        return cls(video_info["id"], video_info["title"], video_info["thumbnail"])

    @classmethod
    @_return_none_on_error_wrapper
    @alru_cache(maxsize=None) # do not use functools.cache or else reuses coroutine (crash)
    async def search_for_music(cls, search: str) -> "Music | None":
        """
        Searches youtube for the song

        Returns:
            Music | None: Music if found, else None
        """

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydt = await asyncio.to_thread(
                    ydl.extract_info, f"ytsearch:{search}", download=False
                )
            return cls.from_yt_dlp(ydt)
        except (yt_dlp.DownloadError, KeyError) as e:
            raise MusicNotFoundError(f"Couldn't find music for search: {search}") from e
