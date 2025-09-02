import pytest
from src.Helpers.helper_functions import sanitize_markdown


class TestMarkdownSanitization:
    def test_sanitize_empty_string(self):
        """Test that empty string returns empty string"""
        assert sanitize_markdown("") == ""
    
    def test_sanitize_none(self):
        """Test that None returns None"""
        assert sanitize_markdown(None) == None
    
    def test_sanitize_plain_text(self):
        """Test that plain text without markdown characters remains unchanged"""
        text = "This is plain text with numbers 123 and symbols !@#$%^&()+="
        assert sanitize_markdown(text) == text
    
    def test_sanitize_asterisk_bold(self):
        """Test that asterisks for bold formatting are escaped"""
        assert sanitize_markdown("*bold text*") == "\\*bold text\\*"
        assert sanitize_markdown("**very bold**") == "\\*\\*very bold\\*\\*"
    
    def test_sanitize_underscore_italic(self):
        """Test that underscores for italic formatting are escaped"""
        assert sanitize_markdown("_italic text_") == "\\_italic text\\_"
        assert sanitize_markdown("__underlined__") == "\\_\\_underlined\\_\\_"
    
    def test_sanitize_backtick_code(self):
        """Test that backticks for code formatting are escaped"""
        assert sanitize_markdown("`inline code`") == "\\`inline code\\`"
        assert sanitize_markdown("```code block```") == "\\`\\`\\`code block\\`\\`\\`"
    
    def test_sanitize_tilde_strikethrough(self):
        """Test that tildes for strikethrough formatting are escaped"""
        assert sanitize_markdown("~~strikethrough~~") == "\\~\\~strikethrough\\~\\~"
    
    def test_sanitize_pipe_spoiler(self):
        """Test that pipes for spoiler formatting are escaped"""
        assert sanitize_markdown("||spoiler text||") == "\\|\\|spoiler text\\|\\|"
    
    def test_sanitize_square_brackets_links(self):
        """Test that square brackets for link formatting are escaped"""
        assert sanitize_markdown("[link text](url)") == "\\[link text\\](url)"
    
    def test_sanitize_angle_brackets_mentions(self):
        """Test that angle brackets for mentions/channels are escaped"""
        assert sanitize_markdown("<@123456789>") == "\\<@123456789\\>"
        assert sanitize_markdown("<#123456789>") == "\\<#123456789\\>"
    
    def test_sanitize_backslash(self):
        """Test that backslashes are escaped (and must be first to avoid double-escaping)"""
        assert sanitize_markdown("text\\with\\backslashes") == "text\\\\with\\\\backslashes"
    
    def test_sanitize_combined_markdown(self):
        """Test complex text with multiple markdown characters"""
        text = "*bold* _italic_ `code` ~~strike~~ ||spoiler|| [link] <mention>"
        expected = "\\*bold\\* \\_italic\\_ \\`code\\` \\~\\~strike\\~\\~ \\|\\|spoiler\\|\\| \\[link\\] \\<mention\\>"
        assert sanitize_markdown(text) == expected
    
    def test_sanitize_real_world_example(self):
        """Test with a real-world video caption example"""
        text = "Check out this *amazing* video! Use code `SAVE20` for ~~50%~~ 20% off! [Click here] <@everyone>"
        expected = "Check out this \\*amazing\\* video! Use code \\`SAVE20\\` for \\~\\~50%\\~\\~ 20% off! \\[Click here\\] \\<@everyone\\>"
        assert sanitize_markdown(text) == expected
    
    def test_sanitize_youtube_title_example(self):
        """Test with typical YouTube title characters"""
        text = "How to *actually* code: A _comprehensive_ guide [2024] - Part 1/3"
        expected = "How to \\*actually\\* code: A \\_comprehensive\\_ guide \\[2024\\] - Part 1/3"
        assert sanitize_markdown(text) == expected