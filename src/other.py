import os
from src.downloader import VIDEO_RETURN_TYPE, AlternateVideoDownloader


class UnknownAlternateDownloader(AlternateVideoDownloader):
    @classmethod
    async def download_video_from_link(
        cls, url: str, path: str | None = None
    ) -> VIDEO_RETURN_TYPE:
        if path is None:
            path = os.path.join("downloads", "other")

        os.makedirs(path, exist_ok=True)

        ydt_opts = {
            "outtmpl": os.path.join(path, "%(id)s.%(ext)s"),
            "noplaylist": True,
            "default_search": "auto",
            "nooverwrites": False, # We may have a video with the same id from a different source
            "quiet": True,
        }

        return await cls._get_list_from_ydt(url, ydt_opts, path)
