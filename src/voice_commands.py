__package__ = "src"
import os
import threading
from queue import LifoQueue, Queue
from typing import Any

import discord
import yt_dlp

from Constants import CYAN
from src import Youtube
from src.voice_helpers import play_path_queue_guild

MISSING = discord.utils.MISSING
last_played = Youtube.get_last_played_guilded()
play_path_queue: Queue[tuple[dict[str, Any], str]] = Queue(8)

queues = play_path_queue_guild()


async def leave(interaction: discord.Interaction):
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message(
            "Bu komutu kullanmak için sunucuda olman gerek.", ephemeral=True
        )
        return

    voice = interaction.guild.voice_client
    if voice is None or not isinstance(voice, discord.VoiceClient):
        await interaction.response.send_message(
            "Ses kanalında değilim.", ephemeral=True
        )
        return

    if interaction.user.voice is None or interaction.user.voice.channel is None:
        await interaction.response.send_message(
            "Ses kanalında değilsin.", ephemeral=True
        )
        return

    if voice.is_playing():
        await interaction.response.send_message(
            "Şu anda bir şey çalıyorum.", ephemeral=True
        )
        return

    if voice.channel.id != interaction.user.voice.channel.id:
        await interaction.response.send_message(
            f"Bot ile aynı kanalda değilsin. Botun kanalı: {voice.channel.mention}"
        )
        return

    channel = voice.channel
    await voice.disconnect()
    embed = discord.Embed(
        title="Ayrıldı", description=f"Bot başarıyla {channel.mention} adlı kanaldan ayrıldı.", color=CYAN
    )
    await interaction.response.send_message(embed=embed)


async def join(interaction: discord.Interaction, channel: discord.VoiceChannel = MISSING, only_respond_on_fail: bool = False):  # -> Union(tuple[bool, discord.VoiceClient], None) cannot use because of python 3.9
    """
    Returns: Returns True if it has responded to the interaction, False if it hasn't.
    """
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message(
            "Bu komutu kullanmak için sunucuda olman gerek.", ephemeral=True
        )
        return True, None

    if channel is MISSING:
        if interaction.user.voice is None or interaction.user.voice.channel is None:
            await interaction.response.send_message(
                "Ses kanalında değilsin.", ephemeral=True
            )
            return True, None
        channel = interaction.user.voice.channel  # type: ignore  # You can put guild_voice_channel as vc

    voice = interaction.guild.voice_client
    if voice is not None and isinstance(voice, discord.VoiceClient):
        if voice.channel.id == channel.id:
            if not only_respond_on_fail:
                await interaction.response.send_message(
                    "Zaten bu kanaldayım.", ephemeral=True
                )
                return True, voice
            return False, voice

        if voice.is_playing() and not only_respond_on_fail:
            await interaction.response.send_message(
                "Şu anda bir şey çalıyorum.", ephemeral=True
            )
            return True, voice

        await voice.move_to(channel)

        if not only_respond_on_fail:
            await interaction.response.send_message(
                f"{voice.channel.mention} kanalına taşındım."
            )
            return True, voice

        return False, voice

    # voice is none or at least a non voice client (which is None for me)
    voice = await channel.connect()
    if only_respond_on_fail:
        return False, voice
    await interaction.response.send_message(
        f"{voice.channel.mention} adlı kanala katıldım."
    )
    return True, voice


async def pause(
    interaction: discord.Interaction, edit: bool = False, stop: bool = False
):
    """
    Warning: WILL NOT RESPOND IF STOP IS TRUE
    """
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message(
            "Bu komutu kullanmak için sunucuda olman gerek.", ephemeral=True
        )
        return

    voice = interaction.guild.voice_client
    if voice is None or not isinstance(voice, discord.VoiceClient):
        await interaction.response.send_message(
            "Bot zaten bir sesli kanalda değil", ephemeral=True
        )
        return

    if not voice.is_playing():
        await interaction.response.send_message(
            "Şu anda bir şey çalmıyorum.", ephemeral=True
        )
        return

    if stop:
        voice.stop()
        return

    from src import views

    view = views.voice_pause_view(timeout=None)
    embed = discord.Embed(title="Şarkı duraklatıldı", color=CYAN)
    played = last_played.get_video_data(interaction.guild.id)
    if played.has_data():
        embed.set_thumbnail(url=played.thumbnail_url)
        embed.add_field(name="Şarkı", value=played.title, inline=False)
    voice.pause()
    if edit:
        await interaction.response.edit_message(content=None, view=view, embed=embed)
        return
    await interaction.response.send_message(embed=embed, view=view)


async def resume(interaction: discord.Interaction, edit: bool = False):
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message(
            "Bu komutu kullanmak için sunucuda olman gerek.", ephemeral=True
        )
        return

    voice = interaction.guild.voice_client
    if voice is None or not isinstance(voice, discord.VoiceClient):
        await interaction.response.send_message(
            "Bot zaten bir sesli kanalda değil", ephemeral=True
        )
        return

    if not voice.is_paused():
        await interaction.response.send_message(
            "Şu anda bir şey durdurulmamış.", ephemeral=True
        )
        return
    from src import views

    view = views.voice_play_view(timeout=None)
    embed = discord.Embed(title="Şarkı devam ettirildi", color=CYAN)
    played = last_played.get_video_data(interaction.guild.id)
    if played.has_data():
        embed.set_thumbnail(url=played.thumbnail_url)
        embed.add_field(name="Şarkı", value=played.title, inline=False)
    if edit:
        await interaction.edit_original_response(content=None, view=view, embed=embed)
        return
    await interaction.response.send_message(embed=embed, view=view)


async def play(interaction: discord.Interaction, search: str):
    responded, voice = await join(interaction, only_respond_on_fail=True)
    if responded or voice is None or interaction.guild_id is None:
        print("responded or voice is None or interaction.guild_id is None")
        return
    if not interaction.response.is_done():
        await interaction.response.defer()

    run_next = create_next(interaction)

    if (
        (not queues.empty(interaction.guild_id) and voice.is_playing())
        or voice.is_playing()
        or voice.is_paused()
    ):
        await add_to_queue(interaction, search)
        return

    with yt_dlp.YoutubeDL() as ydl:
        ydt = ydl.extract_info(f"ytsearch:{search}", download=False)

    if ydt is None:
        await interaction.followup.send(
            f"Youtube da **{search}** hakkında bir şey bulamadım.", ephemeral=True
        )
        return

    info: dict = ydt["entries"][0]
    video_id = info["id"]
    url = info["webpage_url"]

    from src import views

    voice_view = views.voice_play_view(timeout=info["duration"] + 5)

    video_path = f"cache/{video_id}.mp3"
    last_played.set_video_data(
        interaction.guild_id, Youtube.video_data(info["title"], info["thumbnail"])
    )

    if os.path.isfile(video_path):  # video is cached and can be played
        voice.play(discord.FFmpegPCMAudio(video_path), after=run_next)
        embed = discord.Embed(
            title="Şarkı çalınıyor", description=info["title"], url=url, color=CYAN
        )
        embed.set_thumbnail(url=info["thumbnail"])
        await interaction.followup.send(embed=embed, view=voice_view)
        return
    embed = discord.Embed(
        title="Şarkı indiriliyor", description=info["title"], color=CYAN
    )
    sent_message = await interaction.followup.send(embed=embed, wait=True)
    del embed

    queue = LifoQueue()

    thread = threading.Thread(target=Youtube.youtube_download, args=(url, queue, video_path))
    thread.start()
    embed = discord.Embed(
        title="Şarkı indiriliyor", description=info["title"], url=url, color=CYAN
    )
    while thread.is_alive():
        try:
            data = queue.get(
                timeout=60
            )  # wait a minute in case the download fckes up
        except Exception as e:
            await sent_message.edit(content="Şarkı indirilemedi.", embed=None)
            raise e  # re-raise the exception, so I can see it in the logs
        percent_str = str(data["_percent_str"])[8:-4]
        embed.clear_fields().add_field(
            name="İndirme durumu", value=percent_str, inline=False
        )
        await sent_message.edit(embed=embed)
    audio_source = discord.FFmpegPCMAudio(video_path)
    voice.play(audio_source, after=run_next)
    embed = discord.Embed(
        title="Şarkı çalınıyor", description=info["title"], color=CYAN
    )
    embed.set_thumbnail(url=info["thumbnail"])
    await sent_message.edit(embed=embed, view=voice_view)


async def add_to_queue(interaction: discord.Interaction, search: str):
    if (
        interaction.guild_id is None
        or interaction.guild is None
        or not isinstance(interaction.user, discord.Member)
    ):  # all are the same thing but type checking works this way
        await interaction.response.send_message(
            "This command can only be used in a server.", ephemeral=True
        )
        return

    if queues.full(interaction.guild_id):
        await interaction.response.send_message(
            "Şarkı kuyruğu dolu. Lütfen Bekleyin", ephemeral=True
        )
        return

    if not interaction.response.is_done():
        await interaction.response.defer()

    with yt_dlp.YoutubeDL() as ydl:
        ydt = ydl.extract_info(f"ytsearch:{search}", download=False)

    if ydt is None:
        await interaction.followup.send(
            f"Youtube da **{search}** hakkında bir şey bulamadım.", ephemeral=True
        )
        return

    info: dict = ydt["entries"][0]
    video_id = info["id"]
    url = info["webpage_url"]
    video_path = f"cache/{video_id}.mp3"

    if os.path.isfile(video_path):  # the video has been downloaded before
        embed = discord.Embed(
            title="Şarkı Sıraya Eklendi",
            description=f"{info['title']}",
            url=url,
            color=CYAN,
        )
        embed.set_thumbnail(url=info["thumbnail"])
        await interaction.followup.send(embed=embed)
        video = info, video_path
        play_path_queue.put(video)
        return

    extra_queue = LifoQueue()

    t = threading.Thread(
        target=Youtube.youtube_download, args=(url, extra_queue, video_path)
    )
    t.start()

    video = info, video_path

    embed = discord.Embed(
        title="Şarkı Sıraya Eklendi",
        description=f"{info['title']}",
        url=url,
        color=CYAN,
    )
    embed.set_thumbnail(url=info["thumbnail"])
    await interaction.followup.send(embed=embed)

    play_path_queue.put(
        video
    )   # might create a race condition, but I don't care In case it does, it will just download the same video twice.
        # (just implemented it, It won't, install the video twice...)
        # I don't think it will be a problem, but if it is, I will fix it later


def create_next(interaction: discord.Interaction, edit: bool = True):
    def new_next(exception):
        # No exceptions
        if exception is None:
            print("function RAN!")
            interaction.client.loop.create_task(
                next_song(interaction, edit=edit), name="Run Next Song"
            )
        else:
            raise exception

    return new_next


async def next_song(interaction: discord.Interaction, edit: bool = False):
    """
    is used to continue playing the next song in the queue too.
    if there are no more songs in the queue, it will send a message saying so.
    """
    # means the queue has ended
    if play_path_queue.empty():
        from src import views

        view = views.voice_over_view(timeout=None)
        embed = discord.Embed(
            title="Çalma Sırası Bitti",
            description="Çalma sırası bitmiştir, bir şey çalmak için '/çal' komutunu kullanabilirsiniz",
            color=CYAN,
        )
        if edit:
            await interaction.edit_original_response(embed=embed, view=view)
        await interaction.response.send_message(embed=embed, view=view)
        return

    if (
        interaction.guild is None
        or interaction.guild_id is None
        or not isinstance(interaction.user, discord.Member)
    ):
        await interaction.response.send_message("Bu komut sadece sunucularda çalışır.")
        raise RuntimeError("Command run area not server", interaction)

    voice = interaction.guild.voice_client
    if voice is None or not isinstance(voice, discord.VoiceClient):
        await interaction.response.send_message(
            "Bot artık sesli bir kanalda değil Çalma Sırası Temizleniyor...",
            ephemeral=True,
        )
        # clear the queue, as we are not on a voice chat anymore
        print("Clearing Queue")
        with play_path_queue.mutex:
            play_path_queue.queue.clear()
            play_path_queue.all_tasks_done.notify_all()
            play_path_queue.unfinished_tasks = 0
        return

    if voice.is_paused():
        # they just paused the music this runs on any update And I forgor!
        return

    if voice.is_playing():
        voice.stop()
        await interaction.response.defer(thinking=False, ephemeral=True)
        return

    run_next = create_next(interaction)

    info, video_path = play_path_queue.get()

    embed = discord.Embed(title="Şarkı Çalınıyor", description=info["title"], color=CYAN)
    embed.set_thumbnail(url=info["thumbnail"])
    audio_source = discord.FFmpegPCMAudio(video_path)
    voice.play(audio_source, after=run_next)
    play_path_queue.task_done()
    if not edit:
        await interaction.response.send_message(embed=embed)
        return
    from src import views

    view = views.voice_play_view(timeout=int(info["duration"]) + 5)
    await interaction.edit_original_response(content=None, embed=embed, view=view)


async def list_queue(interaction: discord.Interaction):
    """
    Will send the queue ephemerically
    """
    if play_path_queue.empty():
        await interaction.response.send_message("Çalma Sırası Boş", ephemeral=True)
        return
    embed = discord.Embed(title="Çalma Sırası", color=CYAN)
    embed.description = ""
    for i, (info, _) in enumerate(play_path_queue.queue, start=1):
        embed.description = embed.description + f"{i}. {info['title']}\n"
    await interaction.response.send_message(embed=embed, ephemeral=True)