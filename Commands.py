import json
import os
import threading
from datetime import datetime
from queue import LifoQueue

import discord
import openai
import yt_dlp
from discord import app_commands

import GPT
import Read
import Youtube
import client
import logging_system
from Constants import CYAN, KYTPBS_TAG
from birthday_helpers import get_user_and_date_from_string

birthdays = client.get_birthdays()
custom_responses = client.get_custom_responses()
last_played = Youtube.get_last_played_guilded()

admin = discord.Permissions().administrator
discord_client = client.get_client_instance()


class voice_commands(app_commands.Group):
  @app_commands.command(name="kanala_katıl",
                        description="sunucuda belirli bir kanala ya da senin olduğun bir kanala katılır")
  async def channel_join(self, interaction: discord.Interaction, channel: discord.VoiceChannel = None):  # type: ignore
    if channel is not None:
      await interaction.response.defer()
      await channel.connect()
      await interaction.followup.send(f'"{channel.mention}" adlı kanala katıldım!')
      return

    if interaction.guild is None:
      await interaction.response.send_message("Bu komutu kullanmak için bir sunucuda olmalısın", ephemeral=True)
      return
    if interaction.user.voice is None:
      interaction.response.send_message("Bir ses kanalında değilsin, ve bir ses kanalı belirtmedin!", ephemeral=True)
      return

    channel = interaction.user.voice.channel
    await channel.connect()
    await interaction.response.send_message(f'"{channel}" adlı kanala katıldım!')

  @app_commands.command(name="dur", description="Sesi durdurur")
  async def dur(self, interaction: discord.Interaction):
    voices = interaction.client.voice_clients
    if not isinstance(interaction.user, discord.Member) or interaction.guild is None:
      await interaction.response.send_message("Bu komutu kullanmak için bir sunucuda olmalısın",
                                              ephemeral=True)
      return
    if interaction.user.voice is None:
      await interaction.response.send_message("Ses Kanalında Değilsin.",
                                              ephemeral=True)
      return

    for i in voices:
      if i.channel == interaction.user.voice.channel:
        voice = i
        break
    else:
      await interaction.response.send_message("Bot ile aynı ses kanalında değilsin!", ephemeral=True)
      return

    if not voice.is_playing():  # type: ignore
      await interaction.response.send_message("Bot Zaten bir Ses Çalmıyor", ephemeral=True)
      return
    voice.pause()  # type: ignore
    embed = discord.Embed(title="Ses Durduruldu", color=CYAN)
    played = last_played.get_video_data(interaction.guild.id)
    if played.has_data():
      embed.set_thumbnail(url=played.thumbnail_url)
      embed.add_field(name="Şarkı", value=played.title, inline=False)
    await interaction.response.send_message(embed=embed)

  @app_commands.command(name="devam_et", description="Sesi devam ettirir")
  async def devam_et(self, interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or interaction.guild is None:
      await interaction.response.send_message("Bu komutu kullanmak için bir sunucuda olmalısın",
                                              ephemeral=True)
      return
    if interaction.user.voice is None:
      await interaction.response.send_message("Ses Kanalında Değilsin.",
                                              ephemeral=True)
      return
    voices = interaction.client.voice_clients

    for voice in voices:
      if voice.channel == interaction.user.voice.channel:
        if isinstance(voice, discord.VoiceClient):
          if voice.is_paused():
            voice = voice
            break
          else:
            await interaction.response.send_message("Durdurulmuş bir ses yok!", ephemeral=True)
            return
        else:
          await interaction.response.send_message("Bot sesi bulunamadı hatası, lütfen tekrar dene!", ephemeral=True)
          return
    else:
      await interaction.response.send_message("Bot ile aynı ses kanaılnda değilsin!", ephemeral=True)
      return

    voice.resume()
    embed = discord.Embed(title=f"{voice.channel.mention} kanalında Ses Devam Ettirildi", color=CYAN)
    played = last_played.get_video_data(interaction.guild.id)
    if played.has_data():
      embed.set_thumbnail(url=played.thumbnail_url)
      embed.add_field(name="Çalınan", value=played.title, inline=False)
    await interaction.response.send_message(embed=embed)

  @app_commands.command(name="çık", description="Ses Kanalından çıkar")
  async def cik(self, interaction: discord.Interaction, zorla: bool = False):
    voices = interaction.client.voice_clients

    if not isinstance(interaction.user, discord.Member) or interaction.guild is None:
      await interaction.response.send_message("Bu komutu bir sunucuda kullanmalısın", ephemeral=True)
      return

    if not isinstance(interaction.user.voice, discord.VoiceState):
      await interaction.response.send_message("Ses Kanalında Değilsin.",
                                              ephemeral=True)
      return

    if zorla and not interaction.user.guild_permissions.administrator:
      await interaction.response.send_message("Bu komutu kullanmak için yönetici olmalısın", ephemeral=True)
      return

    for i in voices:
      if not isinstance(i, discord.VoiceClient):
        logging_system.log("Unknown data in voice list!", logging_system.INFO)
        continue

      if i.channel == interaction.user.voice.channel:
        if i.is_playing() and not zorla:
          await interaction.response.send_message(
            "Bot başka bir ses kanalında zaten çalıyor lütfen bitmesini bekle. yönetici isen zorla yap", ephemeral=True)
          return
        if i.is_playing() and zorla:
          i.stop()
        await i.disconnect()
        await interaction.response.send_message(f"{i.channel} adlı kanaldan çıktım")
        return

      if i.guild == interaction.guild:
        if zorla:
          if i.is_playing():
            i.stop()
          await i.disconnect()
          await interaction.response.send_message(f"{i.channel} adlı kanaldan çıktım")
          return

        if interaction.user.guild_permissions.administrator:
          await interaction.response.send_message("Botla aynı kanalda değilsin, zorla kullanarak çıkabilirsin",
                                                  ephemeral=True)
          break

        await interaction.response.send_message("Bot ile aynı kanalda değilsin", ephemeral=True)

    else:
      await interaction.response.send_message(
        f'Bot zaten {interaction.guild.name} adlı sunucuda bir sesli kanalda değil!', ephemeral=True)

  @app_commands.command(name="çal", description="Youtubedan bir şey çalmanı sağlar")
  async def cal(self, interaction: discord.Interaction, message: str, zorla: bool = False):
    voices = interaction.client.voice_clients

    if not isinstance(interaction.user, discord.Member) or interaction.guild is None:
      await interaction.response.send_message("Youtube çalma sadece sunucularda çalışır", ephemeral=True)
      return

    if zorla and not interaction.user.guild_permissions.administrator:
      await interaction.response.send_message("Bu komutu zorla kullanmak için yönetici olmalısın.",
                                              ephemeral=True)
      return

    if not isinstance(interaction.guild, discord.Guild):
      await interaction.response.send_message("Youtubedan çalma sadece sunucularda çalışır.", ephemeral=True)
      return

    if interaction.user.voice is None:
      await interaction.response.send_message("Ses Kanalında Değilsin.",
                                              ephemeral=True)
      return

    if not isinstance(interaction.user.voice.channel, discord.VoiceChannel):
      await interaction.response.send_message("Ses Kanalında Değilsin.",
                                              ephemeral=True)
      return

    for i in voices:
      if not isinstance(i, discord.VoiceClient):
        logging_system.log("Unknown thing in voice list")
        continue

      if i.channel == interaction.user.voice.channel:
        if i.is_playing():
          if zorla:
            i.stop()
            voice = i
            break
          if interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Bot zaten çalıyor. zorla yaparak değiştirebilirsin",
                                                    ephemeral=True)
          await interaction.response.send_message("Bot zaten çalıyor. lütfen bitmesini bekle.", ephemeral=True)
          return
        voice = i
        break

      if i.guild == interaction.guild:
        if zorla:
          await i.disconnect(force=True)
          voice = await interaction.user.voice.channel.connect()
          break

        if not i.is_playing():
          await i.disconnect(force=True)
          voice = await interaction.user.voice.channel.connect()
          break
        else:
          await interaction.response.send_message("Bot başka bir ses kanalında zaten çalıyor lütfen bitmesini bekle.",
                                                  ephemeral=True)
          return

    else:
      voice_channel = interaction.user.voice.channel
      voice = await voice_channel.connect()

    if not isinstance(voice, discord.VoiceClient):
      await interaction.response.send_message("Sese katılım hatası, lütfen tekrar deneyin",
                                              ephemeral=True)
      return

    await interaction.response.defer()
    with yt_dlp.YoutubeDL() as ydl:
      ydt = ydl.extract_info(f"ytsearch:{message}", download=False)

    if ydt is None:
      await interaction.followup.send("Youtube da bulunamadı lütfen tekrar dene!", ephemeral=True)
      return
    info = ydt['entries'][0]
    played = last_played.get_video_data(interaction.guild.id)
    print(f"Played: {played.title} Info: {info['title']}")

    if played.title == info['title']:
      print("Aynı şarkı çalınıyor")
      audio_source = discord.FFmpegPCMAudio(f'{os.getcwd()}/cache/{interaction.guild.id}.mp3')
      voice.play(audio_source)
      embed = discord.Embed(title="Şarkı Çalınıyor", description=f"[{info['title']}]", color=CYAN)
      embed.set_thumbnail(url=info['thumbnail'])
      await interaction.followup.send(embed=embed)
      return
    last_played.set_video_data(guild_id=interaction.guild.id, video_data_instance=Youtube.video_data(yt_dlp_dict=ydt))
    embed = discord.Embed(title="Şarkı indiriliyor", description=f"[{info['title']}]")
    embed.set_thumbnail(url=info['thumbnail'])
    sent_message = await interaction.followup.send(embed=embed, wait=True)

    name = f"{os.getcwd()}/cache/{interaction.guild.id}.mp3"

    queue = LifoQueue()

    t = threading.Thread(target=Youtube.youtube_download, args=(info['webpage_url'], queue, name))
    t.start()
    print("running thread")
    data = queue.get()
    print(f"data status: {data['status']}")
    while data['status'] == 'downloading':
      data = queue.get()
      print(data['_percent_str'])
      embed = discord.Embed(title="Şarkı indiriliyor", description=f"[{info['title']}]", url=info['thumbnail'],
                            color=CYAN)
      print(data['_percent_str'])
      embed.add_field(name="İndirilen", value=str(data['_percent_str']))
      embed.set_thumbnail(url=info['thumbnail'])
      await sent_message.edit(embed=embed)
    # Play the audio in the voice channel
    audio_source = discord.FFmpegPCMAudio(f'{os.getcwd()}/cache/{interaction.guild.id}.mp3')
    voice.play(audio_source)
    embed = discord.Embed(title="Şarkı Çalınıyor", description=f"{info['title']}", color=CYAN)
    embed.set_thumbnail(url=info['thumbnail'])
    await sent_message.edit(embed=embed)


class voice_admin_commands(app_commands.Group):

  @app_commands.command(name="sustur", description='birisini susturmanı sağlar')
  async def mute(self, interaction: discord.Interaction, user: discord.Member):
    if not user.guild == interaction.guild:
      await interaction.response.send_message("Kullanıcı bu sunucuda değil", ephemeral=True)
      return
    if not isinstance(user, discord.Member):
      await interaction.response.send_message("Kullanıcıyı bulamadım lütfen tekrar dene", ephemeral=True)
      return
    await user.edit(mute=True)
    await interaction.response.send_message(f"{user} susturuldu")

  @app_commands.command(name="susturma_kaldır",
                        description="Susturulmuş birinin susturmasını kapatmanı sağlar")
  async def unmute(self, interaction: discord.Interaction, user: discord.Member):
    if not isinstance(user, discord.Member):
      await interaction.response.send_message("Kullanıcıyı bulamadım lütfen tekrar dene", ephemeral=True)
      return
    if user.voice is None:
      await user.edit(mute=False)
      await interaction.response.send_message(f"{user} adlı kişinin sesi açıldı")
    else:
      await interaction.response.send_message(
        f"{user} adlı kişi ses kanalında değil")

  @app_commands.command(name="kanal_değiştir", description="Botu bir ses kanalına taşımanı sağlar")
  async def move(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
    if interaction.guild.voice_client is None:
      await interaction.response.send_message("Bot herhangi bir ses kanalında değil", ephemeral=True)
      return
    await interaction.guild.voice_client.move_to(channel)
    await interaction.response.send_message(f"Bot {channel} adlı kanala taşındı")


class AI_commands(app_commands.Group):
  @app_commands.command(name="soru", description="bota bir soru sor")
  async def chatgpt(self, interaction: discord.Interaction, message: str):
    await interaction.response.defer(ephemeral=False)
    print("ChatGPT istek:", message)
    answer1 = GPT.question(message)
    if answer1 == -1:
      await interaction.followup.send("Bir hata oluştu, lütfen tekrar deneyin", ephemeral=True)
      return
    answer = answer1[['content']]
    print(f"Cevap: {answer}")
    if answer == -1:
      await interaction.followup.send("Bir hata oluştu, lütfen tekrar deneyin", ephemeral=True)
      return
    embed = discord.Embed(title="ChatGPT", description=answer)
    await interaction.followup.send(f"ChatGPT'den gelen cevap: \n ", embed=embed)

  @app_commands.command(name="foto", description="Bir Fotoğraf Oluşturmanı Sağlar")
  async def foto(self, interaction: discord.Interaction, message: str):
    await interaction.response.defer(ephemeral=False)
    embed = discord.Embed(title="Foto", description=f'"{message}" için oluşturulan fotoğraf: ')
    try:
      image = openai.Image.create(prompt=message, n=1)
      if image is not None and isinstance(image, dict):
        images = image["data"]
        image_url = images[0]["url"]
        embed.set_image(url=image_url)
      else:
        embed = discord.Embed(title="HATA", description="Bir hata oluştu: 'image bulunamadı'")
        interaction.response.send_message(embed=embed)
        return

    except openai.InvalidRequestError:
      embed = discord.Embed(title="HATA", description="+18 olduğu için izin verilmedi (kapatılamıyor)")
      interaction.response.send_message(embed=embed)
      return

    except openai.OpenAIError:
      embed = discord.Embed(title="HATA", description="Bir hata oluştu, hata: 'OpenAIError'")
      interaction.response.send_message(embed=embed)
      return

    except Exception as e:
      embed = discord.Embed(title="HATA", description=f"Bir hata oluştu: {e.__class__.__name__}")
      interaction.response.send_message(embed=embed)
      return

    if image is None:
      embed = discord.Embed(title="HATA", description="Bir hata oluştu: 'image bulunamadı'")

    if embed.title == "HATA":
      await interaction.followup.send(embed=embed, ephemeral=True)
    await interaction.followup.send(embed=embed, ephemeral=False)


class Birthday_commands(app_commands.Group):
  @app_commands.command(name="dogumgunu_ekle", description="Doğumgününü eklemeni sağlar")
  async def add_birthday(self, interaction: discord.Interaction, day: str, month: str, year: str, user: discord.Member = None):
    if user is None:
      user = interaction.user
    user_id = user.id
    date = datetime(int(year), int(month), int(day))
    date_string = str(date.year) + "-" + str(date.month) + "-" + str(date.day)
    if user_id in birthdays and birthdays[str(user_id)] is not None:
      await interaction.response.send_message(
        f"{user.mention} adlı kişinin doğum günü zaten '{birthdays[str(user_id)]}' olarak ayarlanmış " +
        f"Değiştirmek için lütfen {KYTPBS_TAG}'ya ulaşın", ephemeral=True)
      return
    birthdays[str(user_id)] = date_string
    with open("birthdays.json", "w") as f:
      json.dump(birthdays, f)
    await interaction.response.send_message(
      f"{user.mention} adlı kişinin doğum günü '{date_string}' olarak ayarlandı")

  @app_commands.command(name="dogumgunu_goster", description="Kişinin doğumgününü gösterir")
  async def show_birthday(self, interaction: discord.Interaction, user: discord.Member):
    user_id = str(user.id)
    if user_id in birthdays and birthdays[user_id] is not None:
      await interaction.response.send_message(f"{user.mention} adlı kişinin doğum günü '{birthdays[user_id]}'")
    else:
      await interaction.response.send_message(f"{user.mention} adlı kişinin doğum günü kayıtlı değil",
                                              ephemeral=True)


class admin_birthday_commands(app_commands.Group):
  @app_commands.command(name="dogumgunu_listele", description="Doğumgünlerini listeler, sadece modlar kullanabilir")
  async def list_birthday(self, interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member):
      await interaction.response.send_message("Bir hata oluştu, lütfen tekrar deneyin", ephemeral=True)
      return

    if interaction.user.guild_permissions.administrator is False:
      await interaction.response.send_message("Bu komutu kullanmak için gerekli iznin yok", ephemeral=True)
      return

    embed = discord.Embed(title="Doğumgünleri", description="Doğumgünleri", color=CYAN)
    new_list = get_user_and_date_from_string(birthdays)
    for user, date in new_list.items():
      embed.add_field(name=f"{user}:", value=f"{date}", inline=False)
    await interaction.response.send_message(embed=embed)

  @app_commands.command(name="doğumgünü_sil",
                        description="Doğumgününü silmeni sağlar")
  async def delete_birthday(self, interaction: discord.Interaction, user: discord.Member):

    if interaction.user != user and not interaction.user.guild_permissions.administrator:
      await interaction.response.send_message("Sadece Kendi Doğumgününü Silebilirsin", ephemeral=True)
      return
    user_id = str(user.id)
    if user_id in birthdays and birthdays[user_id] is not None:
      birthdays.pop(user_id)
      with open("birthdays.json", "w") as f:
        json.dump(birthdays, f)
      await interaction.response.send_message(f"{user.mention} adlı kişinin doğum günü silindi")
    else:
      await interaction.response.send_message(f"{user.mention} adlı kişinin doğum günü zaten kayıtlı değil",
                                              ephemeral=True)


class special_commands(app_commands.Group):
  @app_commands.command(name="olustur", description="botun senin ayarladığın mesajlara cevap verebilmesini sağlar")
  async def create_command(self, interaction: discord.Interaction, text: str, answer: str, degistir: bool = False):
    if custom_responses.get(text) is not None:
      if isinstance(interaction.user, discord.User) or not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(f"Bu mesaja zaten bir cevap var: {custom_responses[text]}, " +
                                                "lütfen başka bir mesaj deneyin",
                                                ephemeral=True)
        return
      if not degistir:
        await interaction.response.send_message(f"Bu mesaja zaten bir cevap var: {custom_responses[text]}, " +
                                                "değiştirmek için komutta 'degistir' argümanını kullanın",
                                                ephemeral=True)
        return
      if degistir:
        if not interaction.user.guild_permissions.administrator:
          await interaction.response.send_message("Bu komutu kullanmak için gerekli iznin yok", ephemeral=True)
          return
        eski_cevap = custom_responses[text]
        custom_responses[text] = answer
        with open("responses.json", "w") as f:
          json.dump(custom_responses, f, indent=4)
        embed = discord.Embed(title="Cevap Değiştirildi", description=f"'{text} : {answer}' a değiştirildi", color=CYAN)
        embed.add_field(name="Eski Cevap", value=eski_cevap, inline=False)
        await interaction.response.send_message(embed=embed)
        return

    custom_responses[text] = answer
    with open("responses.json", "w") as f:
      json.dump(custom_responses, f, indent=4)
    await interaction.response.send_message(f"Yeni bir cevap oluşturuldu. {text} : {answer}")

  @app_commands.command(name="cevaplar", description="Bütün özel eklenmiş cevapları gösterir")
  async def answers(self, interaction: discord.Interaction):
    embed = discord.Embed(title="Özel Cevaplar", description="Özel eklenmiş cevaplar", color=CYAN)
    for key, value in custom_responses.items():
      embed.add_field(name=key, value=value, inline=False)
    await interaction.response.send_message(embed=embed)


class main_tree(app_commands.tree.CommandTree):
  def __int__(self, the_client: discord.Client):
    super().__init__(the_client)

  @app_commands.command()
  async def ping(self, interaction: discord.Interaction):
    interaction.response.send_message(f"Pong: {round(discord_client.latency * 1000)}ms")


tree = main_tree(discord_client)


def get_tree_instance():
  return tree


def setup_commands():
  voice_cmds = voice_commands(name="ses", description="Ses komutları!", guild_only=True)
  admin_voice_cmds = voice_admin_commands(name="admin", description="Adminsen kullanabileceğin ses komutları",
                                          default_permissions=admin, parent=voice_cmds)
  ai_cmds = AI_commands(name="zeki", description="Botu zeki yapan komutlar")
  special_cmds = special_commands(name="özel", description="Bota özel komutlar ekleyip görmen için komutlar")
  tree.add_command(admin_voice_cmds)
  tree.add_command(special_cmds)
  tree.add_command(ai_cmds)
