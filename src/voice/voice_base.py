from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Coroutine

import discord
from discord.utils import MISSING


@dataclass
class InteractionResponse:
    message: str
    # ephemeral nearly always also represents if something failed
    ephemeral: bool = False
    embed: discord.Embed = MISSING
    view: discord.ui.View = MISSING
    delete_after: float | None = None

    def __bool__(self) -> bool:
        return False


class VoiceStateType(Enum):
    NOT_IN_VOICE = auto()
    IN_DIFFERENT_VOICE = auto()
    USER_NOT_IN_VOICE = auto()
    ALREADY_IN_VOICE = auto()
    BUSY_PLAYING = auto()
    PAUSED = auto()

    def get_default_interaction_response(self) -> InteractionResponse:
        default_responses = {
            VoiceStateType.NOT_IN_VOICE: InteractionResponse(
                "Bot bir sesli kanalda değil",
                ephemeral=True,
            ),
            VoiceStateType.BUSY_PLAYING: InteractionResponse(
                "Bot şu an başka bir kanalda bir şey çalmakta, başka zaman dene",
                ephemeral=True,
            ),
            VoiceStateType.USER_NOT_IN_VOICE: InteractionResponse(
                "Ses kanalında değilsin", ephemeral=True
            ),
            VoiceStateType.ALREADY_IN_VOICE: InteractionResponse(
                "Bot zaten bu kanalda", ephemeral=True
            ),
            VoiceStateType.IN_DIFFERENT_VOICE: InteractionResponse(
                "Bot başka bir sesli kanalda",
                ephemeral=True,
            ),
            VoiceStateType.PAUSED: InteractionResponse(
                "Müzik Başka bir şey çalarken duraklatılmış.", ephemeral=True
            ),
        }
        # we should never get hit with the unknown error, unless a new state is added and forgotten to be given a default response
        return default_responses.get(
            self, InteractionResponse("Bilinmeyen bir hata oluştu, lütfen bildirin")
        )


@dataclass
class VoiceConnectionResult:
    client: discord.VoiceClient
    state: VoiceStateType | None = None


@dataclass
class VoiceConnectionGetter:
    get_connection: Callable[..., Coroutine[None, None, VoiceConnectionResult]]


VoiceStateTuple = tuple[VoiceStateType, discord.VoiceClient]


def get_voice(
    user: discord.Member,
) -> VoiceStateTuple:
    """
    Determine the voice state and client based on bot and user voice states.

    Returns a tuple of (VoiceStateType, VoiceClient | None) where:

    1. (USER_NOT_IN_VOICE, None) - Neither bot nor user are in voice
    2. (NOT_IN_VOICE, None) - Bot is not in voice but user is
    3. (BUSY_PLAYING, client) - Bot is playing audio
    4. (PAUSED, client) - Bot is paused in a channel
    4. (USER_NOT_IN_VOICE, client) - Bot is in voice but user isn't
    5. (ALREADY_IN_VOICE, client) - Bot and user are in same channel
    6. (IN_DIFFERENT_VOICE, client) - Bot and user are in different channels
    """
    voice = user.guild.voice_client
    is_user_in_voice = user.voice and user.voice.channel

    if not isinstance(voice, discord.VoiceClient):
        if not is_user_in_voice:
            # easier to have an exception that it will return null only twice
            # than to have an exception that it may "return None"
            # unlike TypeScript, python type hinting is not smart enough to know which states might have None,
            # even if you explicitly tell it with a convoluted Multiple-Union-Type (i.e: a,b | c, None | e,f)
            return VoiceStateType.USER_NOT_IN_VOICE, None  # type: ignore
        return VoiceStateType.NOT_IN_VOICE, None  # type: ignore

    if voice.is_playing() and len(voice.channel.members) > 1:
        return VoiceStateType.BUSY_PLAYING, voice

    if voice.is_paused() and len(voice.channel.members) > 1:
        return VoiceStateType.PAUSED, voice

    if not user.voice or not user.voice.channel:
        return VoiceStateType.USER_NOT_IN_VOICE, voice

    channel = user.voice.channel

    if voice.channel.id == channel.id:
        return VoiceStateType.ALREADY_IN_VOICE, voice

    return VoiceStateType.IN_DIFFERENT_VOICE, voice
