import os
import threading
import discord
import yt_dlp
import Youtube
from queue import Queue, LifoQueue
from typing import Any



from Constants import CYAN

last_played = Youtube.get_last_played_guilded()
play_path_queue: Queue[tuple[dict[str, Any], str]] = Queue(8)


async def leave(interaction: discord.Interaction):
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("Bu komutu kullanmak için sunucuda olman gerek.", ephemeral=True)
        return
    
    voice = interaction.guild.voice_client
    if voice is None or not isinstance(voice, discord.VoiceClient):
        await interaction.response.send_message("Ses kanalında değilim.", ephemeral=True)
        return
    
    if interaction.user.voice is None or interaction.user.voice.channel is None:
        await interaction.response.send_message("Ses kanalında değilsin.", ephemeral=True)
        return
    
    if voice.is_playing():
        await interaction.response.send_message("Şu anda bir şey çalıyorum.", ephemeral=True)
        return
    
    if voice.channel.id != interaction.user.voice.channel.id:
        await interaction.response.send_message(f"Bot ile aynı kanalda değilsin. Botun kanalı: {voice.channel.mention}")
        return


async def join(interaction: discord.Interaction, channel: discord.VoiceChannel = None, only_respond_on_fail: bool = False):  # type: ignore # -> Union(tuple[bool, discord.VoiceClient], None cannot use because of python 3.9
    """
    Returns: Returns True if it has responded to the interaction, False if it hasn't.
    """
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("Bu komutu kullanmak için sunucuda olman gerek.", ephemeral=True)
        return True, None
    
    if channel is None:
        if (interaction.user.voice is None or interaction.user.voice.channel is None):
            await interaction.response.send_message("Ses kanalında değilsin.", ephemeral=True)
            return True, None
        channel = interaction.user.voice.channel # type: ignore
    
    voice = interaction.guild.voice_client
    if voice is not None and isinstance(voice, discord.VoiceClient):
        if voice.channel.id == channel.id:
            if not only_respond_on_fail:
                await interaction.response.send_message("Zaten bu kanaldayım.", ephemeral=True)
                return True, voice
            return False, voice
        
        if voice.is_playing() and not only_respond_on_fail:
            await interaction.response.send_message("Şu anda bir şey çalıyorum.", ephemeral=True)
            return True, voice
        
        
        await voice.move_to(channel)
        
        if not only_respond_on_fail:
            await interaction.response.send_message(f"{voice.channel.mention} kanalına taşındım.")
            return True, voice
        
        return False, voice
    
    # voice is none or at least a non voice client (which is None for me)
    voice = await channel.connect()
    if only_respond_on_fail:
        return False, voice
    await interaction.response.send_message(f"{voice.channel.mention} adlı kanala katıldım.")
    return True, voice


async def pause(interaction: discord.Interaction, edit: bool = False, stop: bool = False):
    """
    Warning: WILL NOT RESPOND IF STOP IS TRUE
    """
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("Bu komutu kullanmak için sunucuda olman gerek.", ephemeral=True)
        return
    
    voice = interaction.guild.voice_client
    if voice is None or not isinstance(voice, discord.VoiceClient):
        await interaction.response.send_message("Bot zaten bir sesli kanalda değil", ephemeral=True)
        return
    
    if not voice.is_playing():
        await interaction.response.send_message("Şu anda bir şey çalmıyorum.", ephemeral=True)
        return
    
    if stop:
        voice.stop()
        return
    
    import views
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
        await interaction.response.send_message("Bu komutu kullanmak için sunucuda olman gerek.", ephemeral=True)
        return
    
    voice = interaction.guild.voice_client
    if voice is None or not isinstance(voice, discord.VoiceClient):
        await interaction.response.send_message("Bot zaten bir sesli kanalda değil", ephemeral=True)
        return
    
    if not voice.is_paused():
        await interaction.response.send_message("Şu anda bir şey durdurulmamış.", ephemeral=True)
        return
    import views
    view = views.voice_pause_view(timeout=None)
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
    
    if (not play_path_queue.empty() and voice.is_playing()) or voice.is_playing() or voice.is_paused():
        await add_to_queue(interaction, search)
        return
    
    if not play_path_queue.empty():
        raise RuntimeError("WHY THE FCK DID IT CONTINUE")
    
    with yt_dlp.YoutubeDL() as ydl:
        ydt = ydl.extract_info(f"ytsearch:{search}", download=False)
    
    if ydt is None:
        await interaction.followup.send(f"Youtube da **{search}** hakkında bir şey bulamadım.", ephemeral=True)
        return
    
    info: dict = ydt['entries'][0]
    video_id = info['id']
    url = info['webpage_url']
    
    import views
    voice_view = views.voice_play_view(timeout=info['duration'] + 5)
    
    video_path = f"cache\\{video_id}.mp3"
    last_played.set_video_data(interaction.guild_id, Youtube.video_data(info['title'], info['thumbnail']))
    
    if os.path.isfile(video_path):  # video is cached and can be played
        voice.play(discord.FFmpegPCMAudio(video_path), after=run_next)
        embed = discord.Embed(title="Şarkı çalınıyor", description=info['title'], url=url, color=CYAN)
        embed.set_thumbnail(url=info['thumbnail'])
        await interaction.followup.send(embed=embed, view=voice_view)
        return
    embed = discord.Embed(title="Şarkı indiriliyor", description=info['title'], color=CYAN)
    sent_message = await interaction.followup.send(embed=embed, wait=True)
    del embed
    
    queue = LifoQueue()
    
    t = threading.Thread(target=Youtube.youtube_download, args=(url, queue, video_path))
    t.start()
    embed = discord.Embed(title="Şarkı indiriliyor", description=info['title'], url=url, color=CYAN)
    while t.is_alive():
        try:
            data = queue.get(timeout=120) # wait 2 minutes in case the download fckes up
        except Exception as e:
            await sent_message.edit(content="Şarkı indirilemedi.", embed=None)
            raise e # re-raise the exception so I can see it in the logs
        percent_str = str(data['_percent_str'])[8:-4]
        embed.clear_fields().add_field(name="İndirme durumu", value=percent_str, inline=False)
        await sent_message.edit(embed=embed)
    audio_source = discord.FFmpegPCMAudio(video_path)
    voice.play(audio_source, after=run_next)
    embed = discord.Embed(title="Şarkı çalınıyor", description=info['title'], color=CYAN)
    embed.set_thumbnail(url=info['thumbnail'])
    await sent_message.edit(embed=embed, view=voice_view)


async def add_to_queue(interaction: discord.Interaction, search: str):
    if play_path_queue.full():
        await interaction.response.send_message("Şarkı kuyruğu dolu. Lütfen Bekleyin", ephemeral=True)
        return
    
    if not interaction.response.is_done():
        await interaction.response.defer()
    
    with yt_dlp.YoutubeDL() as ydl:
        ydt = ydl.extract_info(f"ytsearch:{search}", download=False)
    
    if ydt is None:
        await interaction.followup.send(f"Youtube da **{search}** hakkında bir şey bulamadım.", ephemeral=True)
        return

    info: dict = ydt['entries'][0]
    video_id = info['id']
    url = info['webpage_url']
    video_path = f"cache\\{video_id}.mp3"
    
    if os.path.isfile(video_path):  # the video has been downloaded before
        embed = discord.Embed(title="Şarkı Sıraya Eklendi", description=f"{info['title']}", url=url ,color=CYAN)
        embed.set_thumbnail(url=info['thumbnail'])
        await interaction.followup.send(embed=embed)
        video = info, video_path
        play_path_queue.put(video)
        return
    
    extra_queue = LifoQueue()

    t = threading.Thread(target=Youtube.youtube_download, args=(url, extra_queue, video_path))
    t.start()
    
    video = info, video_path
    
    embed = discord.Embed(title="Şarkı Sıraya Eklendi", description=f"{info['title']}", url=url, color=CYAN)
    embed.set_thumbnail(url=info['thumbnail'])
    await interaction.followup.send(embed=embed)
    
    play_path_queue.put(video)  # might create a race contidion but I don't care In case it does, it will just download the same video twice


def create_next(interaction: discord.Interaction, edit: bool = True):
    
    def new_next(e):
        # No exceptions
        if e is None:
            async def next2():
                await next(interaction, edit=edit)
            print("function RAN!")
            task = interaction.client.loop.create_task(next(interaction, edit=edit), name="Run Next Song")
            task.add_done_callback(lambda _: print(f"{_.get_name()} is complete"))
        else:
            raise e
    return new_next


async def next(interaction: discord.Interaction, edit: bool = False): # will be used to continue playing the next song in the queue too.
    if play_path_queue.empty():
        embed = discord.Embed(title="Çalma Sırası Bitti", description="Çalma sırası bitmiştir, bir şey çalmak için '/çal' komutunu kullanabilirsiniz", color=CYAN)
        if edit:
            await interaction.edit_original_response(embed=embed, view=None)
        await interaction.response.send_message(embed=embed)
        return
    
    if interaction.guild is None or interaction.guild_id is None or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("Bu komut sadece sunucularda çalışır.")
        raise RuntimeError("Command run area not server", interaction)
    
    voice = interaction.guild.voice_client
    if voice is None or not isinstance(voice, discord.VoiceClient):
        await interaction.response.send_message("Bot artık sesli bir kanalda değil Çalma Sırası Temizleniyor...", ephemeral=True)
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

    embed = discord.Embed(title="Şarkı Çalınıyor", description=info['title'])
    embed.set_thumbnail(url=info['thumbnail'])
    audio_source = discord.FFmpegPCMAudio(video_path)
    voice.play(audio_source, after=run_next)
    play_path_queue.task_done()
    if not edit:
        await interaction.response.send_message(embed=embed)
        return
    import views
    view = views.voice_play_view(timeout=int(info['duration']) + 5)
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