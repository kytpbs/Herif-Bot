import asyncio
import yt_dlp


class Music:
    def __init__(self, music_id: str, title: str, thumbnail_url: str) -> None:
        from src.voice.download_manager import start_downloading # pylint: disable=import-outside-toplevel # circular import
        self.id = music_id
        self.title = title
        self.thumbnail_url = thumbnail_url

        start_downloading(self)

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
    async def search_for_music(cls, search: str) -> "Music | None":
        """
        Searches youtube for the song

        Returns:
            Music | None: Music if found, else None
        """

        try:
            with yt_dlp.YoutubeDL() as ydl:
                ydt = await asyncio.to_thread(
                    ydl.extract_info, f"ytsearch:{search}", download=False
                )
            return cls.from_yt_dlp(ydt)
        except (yt_dlp.DownloadError, KeyError):
            return None
