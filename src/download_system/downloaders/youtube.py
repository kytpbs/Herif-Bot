import os

from Constants import MAX_VIDEO_DOWNLOAD_SIZE
from src.download_system.downloader import VIDEO_RETURN_TYPE, AlternateVideoDownloader


class YoutubeDownloader(AlternateVideoDownloader):
    @classmethod
    async def download_video_from_link(cls, url: str, path: str | None = None) -> VIDEO_RETURN_TYPE:
        if path is None:
            path = os.path.join("downloads", "youtube")

        os.makedirs(path, exist_ok=True)

        costum_options = {
            'format': f'bestvideo[filesize<{MAX_VIDEO_DOWNLOAD_SIZE}M][ext=mp4]+bestaudio[ext=m4a]/best[filesize<{MAX_VIDEO_DOWNLOAD_SIZE}M][ext=mp4]',
            "outtmpl": os.path.join(path, "%(id)s.mp4"),
            'noplaylist': True,
            'default_search': 'auto',
            'nooverwrites': True,
            'quiet': True,
        }

        return await cls._get_list_from_ydt(url, costum_options, path)
