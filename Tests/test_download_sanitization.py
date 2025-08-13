import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord

from src.download_system.download_commands import _get_caption_and_view
from src.download_system.downloader import VideoFile, VideoFiles
from src.Helpers.helper_functions import sanitize_markdown


class TestDownloadSanitization:
    def test_get_caption_and_view_with_markdown(self):
        """Test that _get_caption_and_view works with sanitized markdown"""
        # Test with a caption that has markdown characters
        markdown_caption = "This is *bold* and _italic_ text with `code`"
        sanitized_caption = sanitize_markdown(markdown_caption)
        expected_sanitized = "This is \\*bold\\* and \\_italic\\_ text with \\`code\\`"
        
        assert sanitized_caption == expected_sanitized
        
        # Test that the sanitized caption can be processed by _get_caption_and_view
        caption, view = _get_caption_and_view(sanitized_caption, True)
        assert caption == sanitized_caption
        
    def test_videofiles_caption_sanitization_integration(self):
        """Test the integration with VideoFiles that have markdown in captions"""
        # Create a mock video file with markdown in the caption
        video_file = VideoFile("/fake/path.mp4", "*bold title* with _italics_")
        video_files = VideoFiles([video_file])
        
        # The caption should contain the markdown characters
        original_caption = video_files.caption
        assert "*bold title* with _italics_" in original_caption
        
        # When sanitized, it should escape the markdown
        sanitized_caption = sanitize_markdown(original_caption)
        assert "\\*bold title\\* with \\_italics\\_" in sanitized_caption
        
    def test_empty_caption_handling(self):
        """Test that empty or None captions are handled correctly"""
        assert sanitize_markdown(None) == None
        assert sanitize_markdown("") == ""
        
        # Test _get_caption_and_view with empty caption
        caption, view = _get_caption_and_view("", True)
        assert caption == ""