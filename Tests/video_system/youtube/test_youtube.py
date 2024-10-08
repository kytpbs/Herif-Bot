import os
import shutil
import pytest

from Tests.video_system.download_tester import DownloadTester
from src.download_system.downloader import DownloadFailedError
from src.download_system.downloaders.youtube import YoutubeDownloader

TEST_YOUTUBE_1 = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

MAIN_FOLDER_PATH = os.path.join("Tests", "video_system", "youtube")
DOWNLOAD_PATH = os.path.join(MAIN_FOLDER_PATH, "downloads")
SHOULD_BE_0 = os.path.join(MAIN_FOLDER_PATH, "dQw4w9WgXcQ.mp4")

class TestYoutubeDownloader(DownloadTester):
    @pytest.fixture(autouse=True)
    def remove_cache(self):
        os.makedirs(DOWNLOAD_PATH, exist_ok=True)
        shutil.rmtree(DOWNLOAD_PATH, ignore_errors=True)
        yield
        #delete the downloads folder
        assert os.path.exists(DOWNLOAD_PATH)
        shutil.rmtree(DOWNLOAD_PATH, ignore_errors=True)

    async def test_basic_download(self):
        try:
            videos = await YoutubeDownloader.download_video_from_link(TEST_YOUTUBE_1, DOWNLOAD_PATH)
        except DownloadFailedError as e:
            assert e.msg
            import warnings
            if "Sign in" not in str(e.with_traceback(None)):
                raise e # re-raise the exception if it's not a sign in error
            warnings.warn(e.msg)
            return
        self.download_single_video_test(videos, SHOULD_BE_0)
