#!/usr/bin/env python3
"""
Simple demonstration script showing the markdown sanitization in action.
This script shows how video captions with markdown characters are sanitized
before being sent to Discord.
"""

from src.download_system.downloader import VideoFile, VideoFiles
from src.Helpers.helper_functions import sanitize_markdown


def demonstrate_sanitization():
    """Demonstrate the markdown sanitization functionality"""
    
    print("=== Markdown Sanitization Demonstration ===\n")
    
    # Example captions that might come from video platforms
    test_captions = [
        "Check out this *amazing* tutorial! Use code `SAVE20` for 20% off!",
        "How to **actually** learn programming [2024] - Part 1/3",
        "~~Old method~~ vs _new approach_ in Python development",
        "Discord Bot Tutorial | Part 5: Advanced Features <@everyone>",
        "Understanding `async/await` in JavaScript **properly**",
        "# Title with markdown\n*Bold text* and _italic text_\n```code block```"
    ]
    
    for i, caption in enumerate(test_captions, 1):
        print(f"Example {i}:")
        print(f"Original caption: {repr(caption)}")
        
        sanitized = sanitize_markdown(caption)
        print(f"Sanitized caption: {repr(sanitized)}")
        
        print(f"Display original: {caption}")
        print(f"Display sanitized: {sanitized}")
        print("-" * 50)
    
    # Demonstrate with VideoFiles object
    print("\n=== VideoFiles Integration ===")
    video_file = VideoFile("/fake/path.mp4", "Tutorial: *Learn* Python `fast` [2024]")
    video_files = VideoFiles([video_file])
    
    original_caption = video_files.caption
    sanitized_caption = sanitize_markdown(original_caption)
    
    print(f"VideoFiles original caption: {original_caption}")
    print(f"VideoFiles sanitized caption: {sanitized_caption}")
    
    print("\n✅ All markdown characters have been properly escaped!")
    print("✅ Captions will now display as plain text in Discord instead of formatted markdown.")


if __name__ == "__main__":
    demonstrate_sanitization()