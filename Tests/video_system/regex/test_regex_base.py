from typing import Type

from src.download_system.downloader import VideoDownloader
from src.download_system.downloading_system import get_downloader


class TestDownloaderRegex:
    def setup(self, downloader_type_to_check: Type[VideoDownloader]) -> None:
        self.downloader_type = downloader_type_to_check # pylint: disable=attribute-defined-outside-init

    def check_link(self, link: str):
        downloader = get_downloader(link)
        return downloader is not None and isinstance(downloader(), self.downloader_type)
