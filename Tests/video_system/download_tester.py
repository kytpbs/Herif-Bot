import subprocess

from pytest import approx

from src.download_system.downloader import VIDEO_RETURN_TYPE, VideoFile


def _get_video_duration(video_path: str) -> float:
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                            "format=duration", "-of",
                            "default=noprint_wrappers=1:nokey=1", video_path],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            check=False)
    return float(result.stdout)


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
        video_duration = _get_video_duration(video.path)
        should_be_duration = _get_video_duration(should_be_path)
        should_be_duration = approx(should_be_duration, rel=0.1) # close enough
        assert video_duration == should_be_duration, f"video_duration was '{video_duration}' should have been: '{should_be_duration}'"
