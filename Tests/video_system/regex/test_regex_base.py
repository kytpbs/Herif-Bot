from typing import Type

from src.downloader import VideoDownloader
from src.downloading_system import get_downloader


class TestDownloaderRegex:
    def setup(self, downloader_type_to_check: Type[VideoDownloader]) -> None:
        self.downloader_type = downloader_type_to_check

    def check_link(self, link: str):
        downloader = get_downloader(link)
        return downloader is not None and isinstance(downloader(), self.downloader_type)
