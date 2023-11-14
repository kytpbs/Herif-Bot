from typing import Any
import discord

from src import Read


def get_general_channel(guild: discord.Guild):
    for channel in guild.text_channels:
        name = channel.name.lower()
        if "genel" in name or "general" in name or "💬" in name:
            return channel
    return None

class DiskDict(dict):
    def __init__(self, filename, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filename = filename
        self.load()

    def save(self):
        Read.write_json(self.filename, self)

    def load(self):
        self.update(Read.json_read(self.filename))

    def __delitem__(self, __key: Any) -> None:
        super().__delitem__(__key)

    def __setitem__(self, __key: Any, __value: Any) -> None:
        super().__setitem__(__key, __value)
        self.save()

    def __getitem__(self, __key: Any, load=False) -> Any:
        if load:
            self.load()
        return super().__getitem__(__key)

    def __del__(self):
        self.save()

    def __enter__(self):
        self.load() # load the file before returning self, as why would they use it using "with" if they didn't want to load it?
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save() # save the file before exiting the "with" block
