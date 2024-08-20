import logging
import os
import shutil

import pytest

from Tests.video_system.download_tester import DownloadTester
from src.instagram import InstagramDownloader

DOWNLOAD_PATH = os.path.join("Tests", "video_system", "instagram", "downloads")

# no params
TEST_REEL_1 = "https://www.instagram.com/reel/C2-vIqjsosW/"
#extra params
TEST_REEL_2 = "https://www.instagram.com/reel/C2-vIqjsosW/?igsh=eGFma20zbWY0bDJs"
#multiple videos
TEST_REEL_3 = "https://www.instagram.com/p/C9tjADzPwDz/?igsh=MnF5dzhjajhxZ3Rs"

class TestInstagramDownloader(DownloadTester):
    @pytest.fixture(autouse=True)
    def remove_all_cache(self):
        logging.basicConfig(level=logging.DEBUG)
        os.makedirs(DOWNLOAD_PATH, exist_ok=True)
        shutil.rmtree(DOWNLOAD_PATH, ignore_errors=True)
        yield
        # delete the downloads folder after the test.
        assert os.path.exists(DOWNLOAD_PATH)
        shutil.rmtree(DOWNLOAD_PATH, ignore_errors=True)

    def test_instagram_single_video_download(self):
        videos = InstagramDownloader.download_video_from_link(
            TEST_REEL_1, path=DOWNLOAD_PATH
        )
        should_be_path = os.path.join("Tests", "video_system", "instagram", "should_be_0.mp4")

        assert videos, "couldn't download, probably due to graphql error (login wasn't successful)"
        self.download_single_video_test(videos, should_be_path)

    def test_instagram_download_extra_params(self):
        videos = InstagramDownloader.download_video_from_link(
            TEST_REEL_2, path=DOWNLOAD_PATH
        )
        should_be_path = os.path.join("Tests", "video_system", "instagram", "should_be_0.mp4")

        self.download_single_video_test(videos, should_be_path)

    def test_instagram_download_multiple_videos(self):
        videos = InstagramDownloader.download_video_from_link(
            TEST_REEL_3, path=DOWNLOAD_PATH
        )

        expected_files = [os.path.join("Tests", "video_system", "instagram", should_be) for should_be in [f"should_be_{i}.mp4" for i in range(1, 7)]]

        self.download_multiple_video_test(videos, expected_files)
