import discord


_TO_BE_DELETED: dict[int, list[discord.Message]] = {}

def add_message_to_be_deleted(guild_id: int | None, message: discord.Message):
    _TO_BE_DELETED.setdefault(guild_id or 0, []).append(message)

async def clear_messages_to_be_deleted(guild_id: int | None):
    messages = _TO_BE_DELETED.pop(guild_id or 0, [])
    for message in messages:
        try:
            await message.delete(delay=0.5)
        except discord.NotFound:
            pass
