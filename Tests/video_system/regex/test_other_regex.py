from src.downloading_system import get_downloader


class TestOtherDownloaderRegex:
    def check_link(self, link: str):
        return get_downloader(link) is not None

    def test_not_supported_links(self):
        assert not self.check_link("https://facebook.com/1234")
        assert not self.check_link(
            "https://www.linkedin.com/posts/microsoft_microsoftlife-microsoftcareersemea-softwareengineerjobs-activity-7231661283509460992-3NLl"
        )
        assert not self.check_link("https://twitch.tv/1234")

    def test_link_like_non_links(self):
        assert not self.check_link("This is not a link")
        assert not self.check_link("alink://link/link")
        assert not self.check_link("https://")
        assert not self.check_link("https://youtube./com/123")
        assert not self.check_link("https://x./com/123")
