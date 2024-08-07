from src.downloading_system import get_downloader
from src.twitter import TwitterDownloader


class TestTwitterRegex:
    def check_link(self, link: str):
        downloader = get_downloader(link)
        return downloader is not None and isinstance(downloader(), TwitterDownloader)

    def test_direct_link(self):
        assert self.check_link("https://x.com/MIT_CSAIL/status/1363172815315214336")

    def test_shortened_link(self):
        assert self.check_link("https://t.co/1234")

    def test_invalid_link(self):
        assert not self.check_link("https://x.com")

    def test_extra_text_link(self):
        assert self.check_link(
            "Dude check this out: https://x.com/MIT_CSAIL/status/1363172815315214336"
        )

    def test_non_link(self):
        assert not self.check_link("This is not a link")

    def test_not_supported_link(self):
        assert not self.check_link("Check this out: https://facebook.com/1234")

    def test_different_type_links(self):
        assert not self.check_link("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert not self.check_link("https://www.instagram.com/p/CMJ1J1JjJjJ/")