import os
import threading
import discord
import yt_dlp
import Youtube
from queue import Queue, LifoQueue
from typing import Optional, Union


from Constants import CYAN

last_played = Youtube.get_last_played_guilded()


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


async def join(interaction: discord.Interaction, channel: discord.VoiceChannel = None, only_respond_on_fail: bool = False) -> Union(tuple[bool, discord.VoiceClient], None):  # type: ignore
    """
    Returns: Returns True if it has responded to the interaction, False if it hasn't.
    """
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("Bu komutu kullanmak için sunucuda olman gerek.", ephemeral=True)
        return True, None
    
    if channel is None and (interaction.user.voice is None or interaction.user.voice.channel is None):
        await interaction.response.send_message("Ses kanalında değilsin.", ephemeral=True)
        return True, None
    
    voice = interaction.guild.voice_client
    if voice is not None and isinstance(voice, discord.VoiceClient):
        if voice.channel.id == channel.id:
            await interaction.response.send_message("Zaten bu kanaldayım.", ephemeral=True)
            return True, None
        
        if voice.is_playing():
            await interaction.response.send_message("Şu anda bir şey çalıyorum.", ephemeral=True)
            return True, None
        
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


async def pause(interaction: discord.Interaction, edit: bool = False):
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
    
    embed = discord.Embed(title="Şarkı duraklatıldı", color=CYAN)
    played = last_played.get_video_data(interaction.guild.id)
    if played.has_data():
        embed.set_thumbnail(url=played.thumbnail_url)
        embed.add_field(name="Şarkı", value=played.title, inline=False)
    if edit:
        await interaction.response.edit_message(content=None, embed=embed)
        return
    await interaction.response.send_message(embed=embed)


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
    embed = discord.Embed(title="Şarkı devam ettirildi", color=CYAN)
    played = last_played.get_video_data(interaction.guild.id)
    if played.has_data():
        embed.set_thumbnail(url=played.thumbnail_url)
        embed.add_field(name="Şarkı", value=played.title, inline=False)
    if edit:
        await interaction.response.edit_message(content=None, embed=embed)
        return
    await interaction.response.send_message(embed=embed)


async def play(interaction: discord.Interaction, search: str):
    responded, voice = await join(interaction, only_respond_on_fail=True)
    if responded or voice is None or interaction.guild_id is None:
        return
    if not interaction.response.is_done():
        await interaction.response.defer()

    with yt_dlp.YoutubeDL() as ydl:
        ydt = ydl.extract_info(f"ytsearch:{search}", download=False)
    
    if ydt is None:
        await interaction.followup.send(f"Youtube da **{search}** hakkında bir şey bulamadım.", ephemeral=True)
        return
    
    info: dict = ydt['entries'][0]
    video_path = f"{os.getcwd()}cache/{info['id']}.mp3"
    last_played.set_video_data(interaction.guild_id, Youtube.video_data(info['title'], info['thumbnail']))
    
    if os.path.isfile(video_path):  # video is cached and can be played
        voice.play(discord.FFmpegPCMAudio(video_path))
        embed = discord.Embed(title="Şarkı çalınıyor", description=info['title'], color=CYAN)
        embed.set_thumbnail(url=info['thumbnail'])
        await interaction.followup.send(embed=embed)
        return
    embed = discord.Embed(title="Şarkı indiriliyor", description=info['title'], color=CYAN)
    sent_message = await interaction.followup.send(embed=embed, wait=True)
    del embed
    
    queue = LifoQueue()
    
    t = threading.Thread(target=Youtube.youtube_download, args=(info['webpage_url'], queue, video_path))
    t.start()
    embed = discord.Embed(title="Şarkı indiriliyor", description=info['title'], color=CYAN)
    data = queue.get(timeout=120) # wait for the first data
    while data['status'] == 'downloading':
        try:
            data = queue.get(timeout=120) # wait 2 minutes in case the download fckes up
        except Exception as e:
            await sent_message.edit(content="Şarkı indirilemedi.", embed=None)
            raise e # re-raise the exception so I can see it in the logs
        percent_str = str(data['_percent_str'])[8:-4]
        embed.clear_fields().add_field(name="İndirme durumu", value=percent_str, inline=False)
        await sent_message.edit(embed=embed)
    audio_source = discord.FFmpegPCMAudio(video_path)
    voice.play(audio_source)
    embed = discord.Embed(title="Şarkı çalınıyor", description=info['title'], color=CYAN)
    embed.set_thumbnail(url=info['thumbnail'])
    await sent_message.edit(embed=embed)
