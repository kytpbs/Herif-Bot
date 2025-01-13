from typing import Callable, Coroutine
import discord

from src.voice.voice_base import InteractionResponse
from src.voice.music_queue import MusicQueue
from src.voice.old_message_holder import (
    add_message_to_be_deleted,
    clear_messages_to_be_deleted,
)


def _voice_button(
    callback: Callable[[], Coroutine[None, None, InteractionResponse]],
    label: str,
    style: discord.ButtonStyle,
) -> discord.ui.Button:
    button = discord.ui.Button(label=label, style=style)

    async def _callback(interaction: discord.Interaction):
        response = await callback()
        await clear_messages_to_be_deleted(interaction.guild_id or 0)
        await interaction.response.send_message(
            response.message,
            embed=response.embed,
            ephemeral=response.ephemeral,
            view=response.view,
            delete_after=response.delete_after,
        )
        add_message_to_be_deleted(
            interaction.guild_id or 0, await interaction.original_response()
        )

    button.callback = _callback
    return button


def skip_button(
    callback: Callable[[], Coroutine[None, None, InteractionResponse]],
) -> discord.ui.Button:
    return _voice_button(callback, "⏭️", discord.ButtonStyle.secondary)


def pause_button(
    callback: Callable[[], Coroutine[None, None, InteractionResponse]],
) -> discord.ui.Button:
    return _voice_button(callback, "⏸️", discord.ButtonStyle.gray)


def resume_button(
    callback: Callable[[], Coroutine[None, None, InteractionResponse]],
) -> discord.ui.Button:
    return _voice_button(callback, "▶️", discord.ButtonStyle.secondary)


def leave_button(
    callback: Callable[[], Coroutine[None, None, InteractionResponse]],
) -> discord.ui.Button:
    return _voice_button(callback, "Çık", discord.ButtonStyle.danger)


def loop_button(
    callback: Callable[[], Coroutine[None, None, InteractionResponse]],
    queue: MusicQueue,
) -> discord.ui.Button:
    return _voice_button(
        callback,
        "🔁",
        discord.ButtonStyle.primary
        if queue.is_looped
        else discord.ButtonStyle.secondary,
    )
