import asyncio
import functools
import logging
from typing import Callable
import discord
from discord.utils import MISSING

from src.voice.voice_base import InteractionResponse, VoiceStateType, get_voice
from src.voice.music_queue import MusicQueue, NoMoreMusic
from src.voice import download_manager
from src.voice.music_base import Music
from src.voice import voice_view_factories
from src.voice.old_message_holder import (
    add_message_to_be_deleted,
    clear_messages_to_be_deleted,
)

# The music queues for each server, as the bot can be in multiple servers at once
MUSIC_QUEUES: dict[int, MusicQueue] = {}
_NOT_SERVER_ERROR_MESSAGE = "Bu komutu kullanmak için sunucuda olman gerek"


async def join(
    interaction: discord.Interaction,
    channel: discord.VoiceChannel | discord.StageChannel = MISSING,
) -> InteractionResponse:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return InteractionResponse(
            _NOT_SERVER_ERROR_MESSAGE,
            ephemeral=True,
        )

    state, voice = get_voice(interaction.user)

    match state:
        case VoiceStateType.NOT_IN_VOICE:
            ...

        case VoiceStateType.IN_DIFFERENT_VOICE:
            await voice.move_to(interaction.user.voice.channel)  # type: ignore # it just works...

        case VoiceStateType.USER_NOT_IN_VOICE:
            if not channel:
                return state.get_default_interaction_response()

        case _:
            return state.get_default_interaction_response()

    if not channel:
        channel = interaction.user.voice.channel

    await channel.connect()
    return InteractionResponse(f"{channel.mention} kanalına katıldım")


async def leave(interaction: discord.Interaction) -> InteractionResponse:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return InteractionResponse(
            _NOT_SERVER_ERROR_MESSAGE,
            ephemeral=True,
        )

    state, voice = get_voice(interaction.user)

    match state:
        case VoiceStateType.USER_NOT_IN_VOICE:
            if not voice:
                return InteractionResponse("Zaten Bir kanalda değilim")

        case VoiceStateType.BUSY_PLAYING:
            if voice.channel != interaction.user.voice.channel:  # type: ignore
                return InteractionResponse(
                    "Başka bir sesli kanalda olduğum için çıkamam", ephemeral=True
                )
            # leave...

        case (
            VoiceStateType.IN_DIFFERENT_VOICE
            | VoiceStateType.ALREADY_IN_VOICE
            | VoiceStateType.PAUSED
        ):
            ...

        case _:
            return state.get_default_interaction_response()

    await voice.disconnect()
    return InteractionResponse("Ses kanalından ayrıldım")


async def pause(interaction: discord.Interaction) -> InteractionResponse:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return InteractionResponse(
            _NOT_SERVER_ERROR_MESSAGE,
            ephemeral=True,
        )

    state, voice = get_voice(interaction.user)

    match state:
        case VoiceStateType.BUSY_PLAYING:
            voice.pause()
            return _get_to_next_state(interaction, MUSIC_QUEUES[interaction.guild.id])

        case VoiceStateType.ALREADY_IN_VOICE | VoiceStateType.IN_DIFFERENT_VOICE:
            return InteractionResponse("Şu anda bir şey çalmıyorum", ephemeral=True)

        case _:
            return state.get_default_interaction_response()


async def resume(interaction: discord.Interaction) -> InteractionResponse:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return InteractionResponse(
            _NOT_SERVER_ERROR_MESSAGE,
            ephemeral=True,
        )

    state, voice = get_voice(interaction.user)

    match state:
        case VoiceStateType.PAUSED:
            voice.resume()
            return _get_to_next_state(interaction, MUSIC_QUEUES[interaction.guild.id])

        case VoiceStateType.ALREADY_IN_VOICE | VoiceStateType.IN_DIFFERENT_VOICE:
            return InteractionResponse("Şu anda bir şey çalmıyorum", ephemeral=True)

        case _:
            return state.get_default_interaction_response()


async def play(interaction: discord.Interaction, search: str) -> InteractionResponse:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return InteractionResponse(
            _NOT_SERVER_ERROR_MESSAGE,
            ephemeral=True,
        )

    state, voice = get_voice(interaction.user)
    queue = MUSIC_QUEUES.setdefault(interaction.guild.id, MusicQueue())

    match state:
        case VoiceStateType.USER_NOT_IN_VOICE:
            if not voice:
                return InteractionResponse(
                    "Ne bot ne sen bir sesli kanaldansın...", ephemeral=True
                )
            # else: user has left the voice channel, but the bot is still in it, so continue

        case VoiceStateType.NOT_IN_VOICE:
            # we try to join the user's voice channel and then play the music
            await join(interaction)
            return await play(
                interaction, search
            )  # recursion, but the state should be different now, so it should work

        case VoiceStateType.BUSY_PLAYING:
            queue = MUSIC_QUEUES.get(interaction.guild.id)
            if not queue:
                raise ValueError(
                    "Bot is playing music, but there is no queue for the server"
                )

            music = await Music.search_for_music(search)
            if not music:
                return InteractionResponse(
                    f"Youtube da **{search}** için bir şey bulamadım", ephemeral=True
                )
            await queue.add_music(music)
            return InteractionResponse(
                f"[{music.title}]({music.url}) aldı şarkı kuyruğa eklendi",
                embed=queue.get_current_song_embed(),
            )

        case VoiceStateType.PAUSED:
            # we try to resume the music then add the music to the queue
            voice.resume()
            await play(
                interaction, search
            )  # recursion, but the state should be different now, so it should work

        case VoiceStateType.ALREADY_IN_VOICE | VoiceStateType.IN_DIFFERENT_VOICE:
            logging.debug("Playing music")

    logging.debug("Playing music2")

    music = await Music.search_for_music(search)
    if not music:
        return InteractionResponse(
            f"Youtube da **{search}** için bir şey bulamadım", ephemeral=True
        )

    await queue.add_music(music)
    while not download_manager.is_downloaded(music):
        # wait for it to download
        if download_manager.is_errored_out(music):
            return InteractionResponse(
                "Şarkı indirilirken bir hata oluştu, lütfen daha sonra tekrar deneyin"
            )
        await asyncio.sleep(1)
    return _get_to_next_state(interaction, queue)


async def skip(interaction: discord.Interaction) -> InteractionResponse:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return InteractionResponse(
            _NOT_SERVER_ERROR_MESSAGE,
            ephemeral=True,
        )

    state, voice = get_voice(interaction.user)

    match state:
        case VoiceStateType.BUSY_PLAYING | VoiceStateType.PAUSED:
            voice.stop()
            return InteractionResponse(
                "Şarkıyı geçtim", ephemeral=True, delete_after=0.6
            )

        case VoiceStateType.ALREADY_IN_VOICE | VoiceStateType.IN_DIFFERENT_VOICE:
            return InteractionResponse("Şu anda bir şey çalmıyorum", ephemeral=True)

        case _:
            return state.get_default_interaction_response()


async def back(interaction: discord.Interaction) -> InteractionResponse:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return InteractionResponse(
            _NOT_SERVER_ERROR_MESSAGE,
            ephemeral=True,
        )

    state, voice = get_voice(interaction.user)

    match state:
        case VoiceStateType.BUSY_PLAYING | VoiceStateType.PAUSED:
            queue = MUSIC_QUEUES.get(interaction.guild.id)
            if not queue:
                raise ValueError(
                    "Bot is playing music, but there is no queue for the server"
                )

            # we go back twice, because when voice.stop() is called, it goes forward once,
            # which makes sence since if there is more music in the queue, it should play that, but we want to go back
            # so we go back twice to actually go back once
            # why did i do it this way? tbh i feel its better than redoing _get_to_next_state just for this
            queue.back_to_previous_music()
            queue.back_to_previous_music()

            voice.stop()
            return InteractionResponse(
                "Önceki şarkıya dönüldü", ephemeral=True, delete_after=0.6
            )

        case VoiceStateType.ALREADY_IN_VOICE | VoiceStateType.IN_DIFFERENT_VOICE:
            return InteractionResponse("Şu anda bir şey çalmıyorum", ephemeral=True)

        case _:
            return state.get_default_interaction_response()


async def toggle_loop(interaction: discord.Interaction) -> InteractionResponse:
    queue = MUSIC_QUEUES.get(interaction.guild_id or 0, MusicQueue())

    queue.is_looped = not queue.is_looped

    embed = queue.get_current_song_embed()
    return InteractionResponse(
        f"Şarkılar {'tekrarlanacak' if queue.is_looped else 'tekrarlanmayacak'}",
        embed=embed,
        view=discord.ui.View()
        .add_item(
            voice_view_factories.pause_button(functools.partial(pause, interaction))
        )
        .add_item(
            voice_view_factories.back_button(functools.partial(back, interaction))
        )
        .add_item(
            voice_view_factories.skip_button(functools.partial(skip, interaction))
        )
        .add_item(
            voice_view_factories.loop_button(
                functools.partial(toggle_loop, interaction), queue
            )
        )
        .add_item(
            voice_view_factories.leave_button(functools.partial(leave, interaction))
        ),
    )


def get_currently_playing_music_message(
    interaction: discord.Interaction,
) -> InteractionResponse:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return InteractionResponse(
            _NOT_SERVER_ERROR_MESSAGE,
            ephemeral=True,
        )

    queue = MUSIC_QUEUES.get(interaction.guild.id, MusicQueue())
    if not queue.queue:
        return InteractionResponse("Şu anda bir şey çalmıyorum", ephemeral=True)

    return _get_currently_playing_message(interaction, queue)


def _get_currently_playing_message(
    interaction: discord.Interaction, queue: MusicQueue
) -> InteractionResponse:
    if not queue.queue:
        return InteractionResponse("Şu anda bir şey çalmıyorum", ephemeral=True)

    return InteractionResponse(
        "",
        embed=queue.get_current_song_embed(),
        view=discord.ui.View()
        .add_item(
            voice_view_factories.pause_button(functools.partial(pause, interaction))
        )
        .add_item(
            voice_view_factories.back_button(functools.partial(back, interaction))
        )
        .add_item(
            voice_view_factories.skip_button(functools.partial(skip, interaction))
        )
        .add_item(
            voice_view_factories.loop_button(
                functools.partial(toggle_loop, interaction), queue
            )
        )
        .add_item(
            voice_view_factories.leave_button(functools.partial(leave, interaction))
        ),
    )


def _get_to_next_state(
    interaction: discord.Interaction, queue: MusicQueue
) -> InteractionResponse:
    """
    Gets the next music and returns the interaction response
    """

    # this should never happen, but type hinting doesn't know that
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        raise ValueError(
            "Interaction is not in a guild, Should never happen in _get_to_next_state"
        )

    state, voice = get_voice(interaction.user)

    match state:
        case VoiceStateType.USER_NOT_IN_VOICE:
            if not voice:
                return InteractionResponse(
                    "Bot bir sesli kanalda değil", ephemeral=True
                )
            # else: user has left the voice channel, but the bot is still in it, so continue

        case VoiceStateType.NOT_IN_VOICE, VoiceStateType.USER_NOT_IN_VOICE:
            if not voice:
                # We lose the MusicQueue if we don't recall get_to_next_state with it anyways.
                return InteractionResponse(
                    "Bot kanaldan atıldı, sırayı temizliyorum", ephemeral=True
                )

        case VoiceStateType.BUSY_PLAYING:
            # User resumed the music, this function gets called again when the music ends, so no worries about queue
            return _get_currently_playing_message(interaction, queue)

        case VoiceStateType.PAUSED:
            # User paused the music, this function gets called again when resumed, so no worries about queue
            current_music = queue.get_current_music()
            embed = discord.Embed(
                title=f"{current_music.title} duraklatıldı",
                description=queue.get_queue_str(),
                color=discord.Color.red(),
                url=current_music.url,
            ).set_thumbnail(url=current_music.thumbnail_url)
            return InteractionResponse(
                "",
                embed=embed,
                view=discord.ui.View()
                .add_item(
                    voice_view_factories.resume_button(
                        functools.partial(resume, interaction)
                    )
                )
                .add_item(
                    voice_view_factories.back_button(
                        functools.partial(back, interaction)
                    )
                )
                .add_item(
                    voice_view_factories.skip_button(
                        functools.partial(skip, interaction)
                    )
                )
                .add_item(
                    voice_view_factories.leave_button(
                        functools.partial(leave, interaction)
                    )
                ),
            )

        case VoiceStateType.ALREADY_IN_VOICE, VoiceStateType.IN_DIFFERENT_VOICE:
            ...  # time to switch to the next music

    try:
        next_music = queue.switch_to_next_music()
    except NoMoreMusic:
        embed = discord.Embed(
            title="Şarkı Kuyruğu Bitti",
            description="Eski Liste",
            color=discord.Color.red(),
        ).add_field(
            name="Çalınan Şarkılar",
            value=queue.get_queue_str(-1),
        )
        queue.clear()  # clear the queue, as we are done with it
        return InteractionResponse("", embed=embed)

    if not next_music.is_downloaded():
        # we don't have the music downloaded yet, most probably due to an error, so we will try to download/retry downloading it
        # if its a loop, it will get replayed, if not loop, bye bye song, cause we can't play it
        download_manager.start_downloading(next_music)
        return _get_to_next_state(interaction, queue)

    voice.play(
            discord.FFmpegPCMAudio(download_manager.get_download_path(next_music)),
            after=_get_to_next_state_interface(interaction, queue),
        )
    return _get_currently_playing_message(interaction, queue)



async def _run_next_state(interaction: discord.Interaction, queue: MusicQueue) -> None:
    """
    Interface function that gives a function that calls the actual function
    """
    interaction_response = _get_to_next_state(interaction, queue)

    await clear_messages_to_be_deleted(interaction.guild_id or 0)

    message = await interaction.followup.send(
        content=interaction_response.message,
        embed=interaction_response.embed,
        view=interaction_response.view,
        wait=True,
    )
    logging.debug("Message sent: %s", message.id)
    add_message_to_be_deleted(interaction.guild_id, message)


def _get_to_next_state_interface(
    interaction: discord.Interaction, queue: MusicQueue
) -> Callable[[Exception | None], None]:
    """
    Interface function that gives a function that calls the actual function
    """

    def call(exception: Exception | None):
        if exception:
            # i will try to get to the next state anyways, hoping for the best, but logging the error
            logging.error(
                "An error occurred while trying to get to the next state",
                exc_info=exception,
            )
        interaction.client.loop.create_task(_run_next_state(interaction, queue))

    return call
