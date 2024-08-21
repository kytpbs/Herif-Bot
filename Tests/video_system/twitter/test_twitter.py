import os
import shutil

import pytest

from Tests.video_system.download_tester import DownloadTester
from src.twitter import TwitterDownloader

DOWNLOAD_PATH = os.path.join("Tests", "video_system", "twitter", "downloads")
SHOULD_BE_FILES_PATH = os.path.join("Tests", "video_system", "twitter")

# no lang=en
TEST_TWEET_1 = "https://x.com/MIT_CSAIL/status/1363172815315214336"
# lang=en added
TEST_TWEET_2 = "https://x.com/MIT_CSAIL/status/1363172815315214336?lang=en"
# multiple videos
TEST_TWEET_3 = "https://x.com/kytpbs1/status/1820227127532220806"


class TestTwitterDownloader(DownloadTester):
    @pytest.fixture(autouse=True)
    def remove_all_cache(self):
        os.makedirs(DOWNLOAD_PATH, exist_ok=True)
        shutil.rmtree(DOWNLOAD_PATH, ignore_errors=True)
        yield
        # delete the downloads folder after the test.
        assert os.path.exists(DOWNLOAD_PATH)
        shutil.rmtree(DOWNLOAD_PATH, ignore_errors=True)

    async def test_twitter_single_video_download(self):
        videos = await TwitterDownloader.download_video_from_link(
            TEST_TWEET_1, path=DOWNLOAD_PATH
        )
        should_be_path = os.path.join(SHOULD_BE_FILES_PATH, "should_be_0.mp4")

        self.download_single_video_test(videos, should_be_path)

    async def test_twitter_download_extra_params(self):
        videos = await TwitterDownloader.download_video_from_link(
            TEST_TWEET_2, path=DOWNLOAD_PATH
        )
        should_be_path = os.path.join(SHOULD_BE_FILES_PATH, "should_be_0.mp4")

        self.download_single_video_test(videos, should_be_path)

    async def test_twitter_download_multiple_videos(self):
        videos = await TwitterDownloader.download_video_from_link(
            TEST_TWEET_3, path=DOWNLOAD_PATH
        )

        expected_files = [os.path.join(SHOULD_BE_FILES_PATH, should_be) for should_be in ["should_be_1.mp4", "should_be_2.mp4"]]

        self.download_multiple_video_test(videos, expected_files)
