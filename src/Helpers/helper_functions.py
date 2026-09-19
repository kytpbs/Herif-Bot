import atexit
from datetime import UTC, datetime, timedelta
import logging
from typing import Any, TypeVar
import discord

from src.Helpers.global_errors import NoGuildContextInGuildCommandError
from src import Read




def assert_guild_membered(
    interaction: discord.Interaction,
) -> tuple[discord.Member, int]:
    if not isinstance(interaction.user, discord.Member) or not interaction.guild_id:
        raise NoGuildContextInGuildCommandError(
            "This command can only be used in a guild context")
        # Raise a new error type and catch in client
    return (interaction.user, interaction.guild_id)


def get_general_channel(guild: discord.Guild):
    for channel in guild.text_channels:
        name = channel.name.lower()
        if "genel" in name or "general" in name or "💬" in name:
            return channel
    return None

async def get_deleting_person(message: discord.Message) -> discord.Member | discord.User:
    if message.guild is None:
        return message.author

    async for entry in message.guild.audit_logs(action=discord.AuditLogAction.message_delete, after=datetime.now(UTC) - timedelta(minutes=2)):
        logging.debug(f'{entry.user} deleted {entry.target} at {entry.created_at}')
        if entry.user is not None:
            return entry.user

    # if we can't find who deleted the message, it was probably the author
    return message.author
K = TypeVar("K")
V = TypeVar("V")
class DiskDict(dict[K, V]):
    def __init__(self, filename: str, *args: Any, **kwargs: Any):
        """Load a JSON-backed mapping and arrange to save it at process exit."""
        super().__init__(*args, **kwargs)
        self.filename = filename
        self.load()
        atexit.register(self.save)

    def save(self):
        Read.write_json(self.filename, self)

    def load(self):
        self.update(Read.json_read(self.filename))

    def __delitem__(self, __key: K) -> None:
        """Delete a key without immediately persisting the change."""
        super().__delitem__(__key)

    def __setitem__(self, __key: K, __value: V) -> None:
        """Set a value and immediately persist the mapping."""
        super().__setitem__(__key, __value)
        self.save()

    def __getitem__(self, __key: K, load: bool = False) -> V:
        """Return a value, optionally reloading the mapping from disk first."""
        if load:
            self.load()
        return super().__getitem__(__key)

    def __enter__(self):
        self.load() # load the file before returning self, as why would they use it using "with" if they didn't want to load it?
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        """Persist the mapping when its context manager exits."""
        del exc_type, exc_val, exc_tb
        self.save() # save the file before exiting the "with" block
