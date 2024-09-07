from typing import AsyncIterator
import discord

from src.gpt_system.gpt_data import Message, MessageHistory, User


async def get_message_history_from_async_iterator(
    message_iterator: AsyncIterator[discord.Message],
) -> MessageHistory:
    message_history: MessageHistory = MessageHistory()

    discord_message_history = [message async for message in message_iterator]
    discord_message_history.reverse()  # reverse the list so that the oldest message is first

    for discord_message in discord_message_history:
        guild_name = discord_message.guild.name if discord_message.guild else None
        user = User(name=discord_message.author.name, is_bot=discord_message.author.bot)
        message = Message(user, discord_message.content, guild_name)
        message_history.append(message)

    return message_history


async def get_message_history_from_discord_channel(
    discord_channel: discord.abc.Messageable, limit: int = 10
) -> MessageHistory:
    return await get_message_history_from_async_iterator(
        discord_channel.history(limit=limit + 1)
    )


async def get_message_history_from_discord_message(
    message: discord.Message,
) -> MessageHistory:
    return await get_message_history_from_discord_channel(message.channel)
