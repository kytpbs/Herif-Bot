from src.downloader import VIDEO_RETURN_TYPE


class DownloadTester:
    def download_single_video_test(self, videos: VIDEO_RETURN_TYPE, should_be_path: str):
        assert len(videos) == 1
        video = videos[0]

        with open(video.path, "rb") as downloaded, open(
            should_be_path, "rb"
        ) as should_be:
            assert downloaded.read() == should_be.read(), "Downloaded file does not match the expected file"

    def download_multiple_video_test(self, videos: VIDEO_RETURN_TYPE, should_be_paths: list[str]):
        assert len(videos) == len(should_be_paths), f"len(videos)={len(videos)} len(should_be_paths)={len(should_be_paths)}"

        for video, should_be_path in zip(videos, should_be_paths):
            with open(video.path, "rb") as downloaded, open(
                should_be_path, "rb"
            ) as should_be:
                assert downloaded.read() == should_be.read(), "Downloaded file does not match the expected file"
