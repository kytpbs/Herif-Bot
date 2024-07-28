import re
from bs4 import BeautifulSoup
import discord

TWITTER_ID_REGEX = r"status/(\d+)"

def convert_paths_to_discord_files(paths: list[str]) -> list[discord.File]:
    return [discord.File(path) for path in paths]

def get_tweet_id(url: str) -> str | None:
    match = re.search(TWITTER_ID_REGEX, url)
    return match.group(1) if match else None

def get_filename_from_data(data: BeautifulSoup) -> str:
    file_name = data.find_all("div", class_="leading-tight")[0].find_all("p", class_="m-2")[0].text # Video file name
    file_name = re.sub(r"[^a-zA-Z0-9]+", ' ', file_name).strip() + ".mp4" # Remove special characters from file name
    return file_name
