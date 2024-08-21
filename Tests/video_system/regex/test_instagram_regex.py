import pytest

from src.instagram import InstagramDownloader
from Tests.video_system.regex.test_regex_base import TestDownloaderRegex


class TestInstagramRegex(TestDownloaderRegex):
    @pytest.fixture(autouse=True)
    def setup_class(self):
        super().setup(InstagramDownloader)

    def test_direct_reel_link(self):
        assert self.check_link("https://www.instagram.com/reel/C2-vIqjsosW")

    def test_direct_post_link(self):
        assert self.check_link("https://www.instagram.com/p/C2-vIqjsosW")

    def test_direct_link_with_params(self):
        assert self.check_link(
            "https://www.instagram.com/p/C2-vIqjsosW/?igsh=eGFma20zbWY0bDJs"
        )
        assert self.check_link(
            "https://www.instagram.com/reel/C2-vIqjsosW/?igsh=eGFma20zbWY0bDJs"
        )

    def test_shortened_link(self):
        assert self.check_link("https://instagr.am/p/C2-vIqjsosW")
        assert self.check_link("https://instagr.am/reel/C2-vIqjsosW")

    def test_extra_text_link(self):
        assert self.check_link(
            "Check this out: https://www.instagram.com/p/C2-vIqjsosW"
        )
        assert self.check_link(
            "Check this out: https://www.instagram.com/reel/C2-vIqjsosW"
        )
        assert self.check_link(
            "Dude look at this video fr fr https://www.instagram.com/reel/C2-vIqjsosW"
        )

    def test_invalid_link(self):
        assert not self.check_link("https://www.instagram.com")

    def test_invalid_link_with_extra(self):
        assert not self.check_link("Look at this: https://www.instagram.com")

    def test_invalid_shortened_link(self):
        assert not self.check_link("https://instagr.am")

    def test_different_type_links(self):
        assert not self.check_link("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert not self.check_link("https://x.com/MIT_CSAIL/status/1363172815315214336")

    def test_non_link(self):
        assert not self.check_link("This is not a link")
