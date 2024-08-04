import logging
from abc import ABC, abstractmethod

_NONE_STRING = "Doesn't exist"


class VideoFile:
    """
    Video object that contains the title, and its file path.
    """
    def __init__(self, file_path: str, title: str | None = None) -> None:
        self._title = title
        self._file_path = file_path

    def __str__(self) -> str:
        return f"Title: {self._title}, File Path: {self._file_path}"
    
    def __repr__(self) -> str:
        return f'Title: {self._title or _NONE_STRING}, File Path: {self._file_path or _NONE_STRING}'

    def __hash__(self) -> int:
        return hash((self._title, self._file_path))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VideoFile):
            return False
        return self._title == other._title and self._file_path == other._file_path

    @property
    def caption(self) -> str | None:
        return self._title
    
    @property
    def path(self) -> str:
        return self._file_path



VIDEO_RETURN_TYPE = list[VideoFile]

class VideoDownloader(ABC):
    """
    INTERPHASE FOR DOWNLOADING CONTENT FROM A WEBSITE
    """

    @staticmethod
    @abstractmethod
    def download_video_from_link(url: str, path: str | None = None) -> VIDEO_RETURN_TYPE:
        """
        Downloads Videos from a url
        if path is None, the default path is downloads/{website_name}

        if the download fails, it returns an empty list
        """
        logging.error(
            "VideoDownloader download_url interface was directly called, this should not happen! url was: %s for path: %s",
            url,
            path,
        )
        return []
