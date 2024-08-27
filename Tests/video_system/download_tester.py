import os
import requests
from src.downloader import VIDEO_RETURN_TYPE, VideoFile


class DownloadTester:
    def download_single_video_test(self, videos: VIDEO_RETURN_TYPE, should_be_path: str):
        assert len(videos) == 1
        video = videos[0]

        self._test_download(video, should_be_path)

    def download_multiple_video_test(self, videos: VIDEO_RETURN_TYPE, should_be_paths: list[str]):
        assert len(videos) == len(should_be_paths), f"len(videos)={len(videos)} len(should_be_paths)={len(should_be_paths)}"

        for video, should_be_path in zip(videos, should_be_paths):
            self._test_download(video, should_be_path)


    def _test_download(self, video: VideoFile, should_be_path: str):
        with open(video.path, "rb") as downloaded, open(
                should_be_path, "rb" # change to "wb" to run fix tests
            ) as should_be:
            # should_be.write(downloaded.read()) # uncomment to fix tests
            assert downloaded.read() == should_be.read(), "Downloaded file does not match the expected file"
