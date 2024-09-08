import pytest

from src.Youtube import YoutubeDownloader
from Tests.video_system.regex.test_regex_base import TestDownloaderRegex


class TestYoutubeRegex(TestDownloaderRegex):
    @pytest.fixture(autouse=True)
    def setup_class(self):
        super().setup(YoutubeDownloader)

    def test_direct_link(self):
        assert self.check_link("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_direct_link_with_timestamp(self):
        assert self.check_link("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s")

    def test_shortened_link(self):
        assert self.check_link("https://youtu.be/dQw4w9WgXcQ")

    def test_shortened_link_with_timestamp(self):
        assert self.check_link("https://youtu.be/dQw4w9WgXcQ?t=10")

    def test_share_parameter_link(self):
        assert self.check_link("https://youtu.be/dQw4w9WgXcQ?si=T3vbuTjMmskB3x3d")

    def test_extra_text_link(self):
        assert self.check_link(
            "Check this out: https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )

    def test_extra_text_link2(self):
        assert self.check_link(
            "Check this out: https://www.youtube.com/watch?v=tvO-LTGIrXo"
        )

    def test_extra_text_url(self):
        assert self.check_link("Check this out: www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_extra_text_url_2(self):
        assert self.check_link("Check this out: www.youtube.com/watch?v=tvO-LTGIrXo")

    def test_invalid_link(self):
        assert not self.check_link("https://www.youtube.com")

    def test_invalid_shortened_link(self):
        assert not self.check_link("https://youtu.be")

    def test_different_type_links(self):
        assert not self.check_link("https://www.instagram.com/p/CMJ1J1JjJjJ/")
        assert not self.check_link("https://x.com/MIT_CSAIL/status/1363172815315214336")
