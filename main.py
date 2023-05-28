import json
import time
import asyncio
import discord
import yt_dlp
import os
import random
import openai
from Read import readFile, jsonRead
from datetime import datetime
from webserver import keep_alive
from discord import app_commands
from discord.ext import tasks, commands
from yt_dlp import YoutubeDL

ydl_opts = {
  'format': 'bestaudio',
}




try:
  import Token
  token = Token.token
except Exception:
  token = os.getenv('TOKEN')
try:
  import OpenAiKey
  openai.api_key = OpenAiKey.token
except Exception:
  openai.api_key = os.getenv('OpenAiKey')
costom1 = readFile("Costom1.txt")
costom2 = readFile("Costom2.txt")
birthdays = jsonRead('birthdays.json')
print(birthdays)
intents = discord.Intents.all()
intents.members = True
intents.voice_states = True
sus_gif = "https://cdn.discordapp.com/attachments/726408854367371324/1010651691600838799/among-us-twerk.gif"
deleted_messages_channel = 991442142679552131
kytpbs_tag = "<@474944711358939170>"
cyan = 0x00FFFF
cya = 696969



class MyClient(discord.Client):

  def __init__(self):
    super().__init__(intents=discord.Intents.all())
    self.synced = False

  async def on_ready(self):
    await self.wait_until_ready()
    check_birthdays.start()
    if not self.synced:
      await tree.sync()
      self.synced = True
    print('Logged on as', self.user)

  async def on_member_join(self, member):
    print(member, "Katıldı! ")
    channel = client.get_channel(929329231173910578)
    if isinstance(channel, discord.TextChannel):
      await channel.send("Salak bir kişi daha servera katıldı... Hoşgelmedin " +
                       member)

  async def on_member_remove(self, member):
    channel = client.get_channel(929329231173910578)
    if isinstance(channel, discord.TextChannel):
      await channel.send("Zeki bir insan valrlığı olan " + "**" + str(member) +
                        "**" + " Bu saçmalık serverdan ayrıldı")
    print(member, "Ayrıldı! ")

  async def on_guild_channel_create(self, channel):
    print("New Channel Created:", channel)
    if str(channel) == "a":
      await channel.send("Kanal 3 saniye içinde siliniyor")
      existing_channel = channel
      print("Deleting Channel " + str(channel) + "in 3 seconds")
      await channel.send("Kanal 3 Saniye İçinde Siliniyor")
      for i in range(3):
        await channel.send(str(3 - i))
        time.sleep(1)
      await channel.send("Siliniyor...")
      await existing_channel.delete()

  async def on_user_update(self, before, after):
    pfp = before.avatar_url
    print("Profil değişti:", before)
    profile_change = discord.Embed(title="Biri profilini deiğiştirdi amk.",
                                   description="Eski Hali: " + str(before) +
                                   "\n Yeni Hali: " + str(after),
                                   color=cya)
    channel = discord.utils.get(client.get_all_channels(), name='boss-silinen')
    profile_change.set_image(url=pfp)
    if isinstance(channel, discord.TextChannel):
      await channel.send(embed=profile_change)

  async def on_member_ban(self, guild, user):
    channel = discord.utils.get(client.get_all_channels(), name='〖💬〗genel')
    if isinstance(channel, discord.TextChannel):
      await channel.send("Ah Lan " + str(user) + " Adlı kişi " + str(guild) +
                        " serverından banlandı ")
    else:
      print("There were an error while sending a message to the channel")
    print("Ah Lan", str(user), "Adlı kişi", str(guild), "serverından banlandı")

  async def on_member_unban(self, guild, user):
    try:
      await user.send("You are finally unbanned from " + str(guild) +
                      " Named server :)")
      print("sending dm to ..." + user + "Server: " + str(guild))
    except Exception:
      print("There were an error while sending a DM")
      channel = discord.utils.get(client.get_all_channels(), name='〖💬〗genel')
      if isinstance(channel, discord.TextChannel):
        await channel.send(
          f"{user} bu mal gibi {guild} sunucusuna geri girebilme hakkı kazanmılştır"
        )
      pass

  async def on_message_edit(self, before, message):
    if message.author == self.user:
      return
    if before.content == message.content:
      return
    
    embed = discord.Embed(title="Mesaj Düzenlendi", description="Biri Mesajını Düzenlendi",color=0x00FFFF)
    
    embed.add_field(name="Kanal: ", value=message.channel, inline=False)
    embed.add_field(name="Kişi: ", value=message.author, inline=False)
    embed.add_field(name="Eski Mesaj: ", value=before.content, inline=False)
    embed.add_field(name="Yeni Mesaj: ", value=message.content, inline=False)

    channel = self.get_channel(deleted_messages_channel)
    if isinstance(channel, discord.TextChannel):
        await channel.send(embed=embed)

  async def on_message_delete(self, message):
    if message.author == self.user:
      return
    
    channel = self.get_channel(deleted_messages_channel)
    
    async for entry in message.guild.audit_logs(
      action=discord.AuditLogAction.message_delete):
      print(f'{entry.user} deleted {entry.target}')
      who_deleted = entry.user
      break
    else:
      who_deleted = None
    
    embed = discord.Embed(
      title="Mesaj silindi.", description="Silinen Mesaj: " + str(message.content),
      color=cya)
    embed.add_field(name="Silinen kanal:", value=message.channel, inline=False)
    embed.add_field(name="Gönderen kişi:", value=message.author, inline=False)
    if who_deleted is not None:
      embed.add_field(name="Silen kişi:", value=who_deleted, inline=False)

    if message.attachments is not None:
      if (len(message.attachments) == 1):
        embed.set_image(url=message.attachments[0].url)
      else:
        for attachment in message.attachments:
          embed.add_field(name=f"Eklentiler:", value=attachment.url, inline=False)
    if message.embeds is not None:
      embeds2 = message.embeds
    else:
      embeds2 = []
    if isinstance(channel, discord.TextChannel):
      await channel.send(embed=embed)
      for embed in embeds2:
        await channel.send(embed=embed)

  async def on_message(self, message):
    x = message.content
    y = x.lower()
    user = message.author
    channel = message.channel
    guild = message.guild
    data = str(guild) + " " + str(channel) + " " + str(user) + ": " + x
    print(data)
    with open("log.txt", "a") as f:
      f.write(str(data) + "\n")

    Time = datetime.now().strftime("%H:%M:")
    if message.author == self.user:
      return

    if Time == "06:11:":  #9:11 for +3 timezone
      await channel.send("🛫🛬💥🏢🏢")
    masaj = y.split(" ")
    masaj_uzunluk = len(masaj)
    son_mesaj = masaj[masaj_uzunluk - 1]
    if son_mesaj == ("nerde") or son_mesaj == ("nerede") or son_mesaj == (
        "neredesin") or son_mesaj == ("nerdesin"):
      print(son_mesaj)
      await message.reply(
        f'Ebenin amında. Ben sonu "{son_mesaj}" diye biten bütün mesajlara cevap vermek için kodlanmış bi botum. Seni kırdıysam özür dilerim.'
      )

    for i in range(1, len(costom1)):
      if x == costom1[i]:
        await message.reply(costom2[i])

    if 'tuna' in y:
      await message.channel.send("<@725318387198197861>")  # tuna tag

    if 'kaya' in y:
      await message.reply("Zeka Kübü")
      await message.channel.send("<@474944711358939170>")  # kaya tag

    if 'neden' in y:
      await message.reply("Kaplumağa Deden :turtle: ")

    if y == "ping":
      await message.reply("pong")
    if y == "31":
      await message.channel.send("sjsjsj")
    if y == "A":
      await message.reply(x)
    if y == "dm":
      await user.send("PING")
    if y == "sus":
      await message.reply(sus_gif)
    if y == "cu":
      await message.reply("Ananın AMCUUUU")
    if y == "mp3":
      discord.FFmpegPCMAudio("test.mp3")
    if y == "array":
      print(f"Array: {costom1}")
      embed = discord.Embed(title="Arraydekiler:", colour=cya)
      for i in range(len(costom1)):
        embed.add_field(name="Yazılan:", value=costom1[i], inline=True)
        embed.add_field(name="Cevaplar:", value=costom2[i] + "\n", inline=True)
      await message.reply(embed=embed)
    if y == "pfp":
      pfp = user.avatar_url
      embed = discord.Embed(title="Profile Foto Test",
                            description="profile: ",
                            type="rich",
                            color=cya)
      embed.set_image(url=pfp)
      await message.channel.send(embed=embed)
    if y == "katıl":
      if user.voice is not None:
        kanal = message.author.voice.channel
        print(str(kanal) + "'a katılınıyor")
        voice = await kanal.connect()
      if user.voice is None:
        await message.channel.send(
          "Bir Ses Kanalında Değilsin... Lütfen Tekrar Dene")
    if y == "çık:":
      if self.voice_clients and self.voice_clients[0]:
        kanal = self.voice_clients[0].channel
        if isinstance(kanal, discord.VoiceProtocol):
          await kanal.disconnect(force=False)
    if y == "rastgele katıl":
      kanallar = guild.voice_channels
      kanal = kanallar[random.randint(1, 11)]
      await kanal.connect()

    if y == "söyle":
      if masaj_uzunluk > 1:
        await message.channel.send(masaj[1])
      else:
        await message.reply("Ne söyleyeyim?")

    if message.content.startswith("oluştur"):
      print("oluştur")
      if len(x.split(" ")) < 2:
        await message.reply("İlk Mesajı girmediniz.")
        return
      if len(x.split(" ")) < 3:
        await message.reply("Son Mesajı Girmediniz")
        return
      print(f"uzunluklar: 1: {len(costom1)} 2:")
      x1 = ['', x.split(" ")[1]]
      x2 = ['', x.split(" ")[2]]
      costom1.append(x.split(" ")[1])
      costom2.append(x.split(" ")[2])
      with open('Costom1.txt', 'a') as f:
        f.writelines('\n'.join(x1))
      with open('Costom2.txt', 'a') as l:
        l.writelines('\n'.join(x2))
      embed = discord.Embed(title="Yeni özel komut oluşturuldu:",
                            description="Test: ",
                            type="rich",
                            color=cya)
      embed.add_field(name="Söylenen: ", value=x.split(" ")[1], inline=True)
      embed.add_field(name="Botun cevabı: ",
                      value=x.split(" ")[2],
                      inline=True)
      await message.reply(embed=embed)
      print(f"1: {costom1} 2: {costom2}")

    if message.content.startswith("sustur"):
      if str(message.author) == "braven#8675":
        await message.reply("Salak Braven")
      else:
        Message = message.content
        name = Message.split(" ")[1]
        member = discord.utils.get(message.guild.members, name=name)
        if member is not None:
          await message.reply(name + " Susturluyor")
          await member.edit(mute=True)
        else:
          await message.reply("Kişi Anlaşılamadı lütfen tekrar deneyin")

    elif message.content.startswith("aç"):
      Message = message.content
      name = Message.split(" ")[1]
      member = discord.utils.get(message.guild.members, name=name)
      if member is not None:
        print(str(message.author))
        if str(message.author) == "braven#8675":
          await message.reply("Salak Braven")
        else:
          await message.reply(name + " Açılıyor")
          await member.edit(mute=False)
          await member.edit(deafen=False)
      else:
        await message.reply("Kişi Anlaşılamadı lütfen tekrar deneyin")

    elif message.content.startswith("sağırlaştır"):
      Message = message.content
      name = Message.split(" ")[1]
      member = discord.utils.get(message.guild.members, name=name)
      if member is not None:
        print(str(message.author))
        if str(message.author) == "braven#8675":
          await message.reply("Salak Braven")
        else:
          await message.reply(name + " Sağırlaştırılıyor")
          await member.edit(deafen=True)
      else:
        await message.reply("Kişi Anlaşılamadı lütfen tekrar deneyin")

    if message.content.startswith("spam"):
      for _ in range(10):
        await message.reply(x.split(" ")[1])
      

keep_alive()
client = MyClient()
general_chat = client.get_channel(1056268428308135976)
tree = app_commands.CommandTree(client)

@tasks.loop(hours=24)
async def check_birthdays():
    channel = client.get_channel(1056268428308135976)
    if not isinstance(channel, discord.TextChannel):
      raise RuntimeError("Kanal Bulunamadı")
    today = datetime.now()
    usuable_dict = get_user_and_date(birthdays)

    for user, birthday in usuable_dict.items():
      if birthday.month == today.month and birthday.day == today.day:
          age = today.year - birthday.year
          print(user)
          await channel.send(f"{user.mention} {age} yaşına girdi. Doğum günün kutlu olsun!")

def get_user_and_date(dict):
  new_dict = {}
  for user_id, date in dict.items():
    user = client.get_user(int(user_id))
    if user is None:
      continue
    dates = date.split("-")
    if len(dates) != 3:
      print("Hatalı tarih formatı, lütfen düzeltin!")
      continue
    date_obj = datetime(int(dates[0]), int(dates[1]), int(dates[2]))
    print(f"{user} : {date_obj}")
    if date_obj is None:
      continue
    new_dict[user] = date_obj

  return new_dict

@tree.command(name="sa", description="Bunu kullanman sana 'as' der")
async def self(interaction: discord.Interaction):
  await interaction.response.send_message("as")


@tree.command(name="katıl", description="Kanala katılmamı sağlar")
async def katil(interaction: discord.Interaction):
  voices = interaction.client.voice_clients

  if not isinstance(interaction.user, discord.Member):  
    await interaction.response.send_message("Bir Hata oluştu, lütfen tekrar deneyin",
                                            ephemeral=True)
    return
  
  if interaction.user.voice is None:
    await interaction.response.send_message("Ses Kanalında Değilsin.",
                                            ephemeral=True)
    return

  for i in voices:
    if i.channel == interaction.user.voice.channel:
      voice = i
      print("Same channel as user")
      await interaction.response.send_message(
        "Zaten seninle aynı ses kanalındayım.", ephemeral=True)
      break
  
  else:
    if interaction.user.voice.channel is None:
      await interaction.response.send_message("Ses Kanalında Değilsin.",
                                              ephemeral=True)
      return
    vc = interaction.user.voice.channel
    voice = await vc.connect()
    await interaction.response.send_message(
      f"{vc} adlı ses kanalına katıldım", ephemeral=False) 

@tree.command(name="rastgele_katıl",
              description="sunucuda rastgele bir kanala katılır")
async def first_command(interaction):
  try:
    kanallar = interaction.guild.voice_channels
    kanal = kanallar[random.randint(1, len(kanallar) - 1)]
    await kanal.connect()
    await interaction.response.send_message(f'"{kanal}" adlı kanala katıldım!')
  except Exception:
    await interaction.response.send_message('bilinmeyen bir hata oluştu!', ephemeral=True)


@tree.command(name="dur", description="Sesi durdurur")
async def dur(interaction: discord.Interaction):
  voices = interaction.client.voice_clients
  if not isinstance(interaction.user, discord.Member):
    await interaction.response.send_message("Bir hata oluştu, lütfen tekrar deneyin",
                                            ephemeral=True)
    return
  if interaction.user.voice is None:
    await interaction.response.send_message("Ses Kanalında Değilsin.",
                                            ephemeral=True)
    return
  for i in voices:
    if i.channel == interaction.user.voice.channel:
      voice = i
      if isinstance(voice, discord.VoiceClient):
        voice.pause()
        await interaction.response.send_message(
          f"{voice.channel} kanaılnda ses durduruldu", ephemeral=False)
        break
  else:
    await interaction.response.send_message("Bot ile aynı ses kanalında değilsin!", ephemeral=True)

@tree.command(name="devam_et", description="Sesi devam ettirir")
async def devam_et(interaction: discord.Interaction):
  if not isinstance(interaction.user, discord.Member):
    await interaction.response.send_message("Bir kullanıcı değilsin hatası, lütfen tekrar deneyin",
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
          await interaction.response.send_message(
          f"{voice.channel} kanaılnda ses devam ettiriliyor")
          voice.resume()
          break
        else:
          await interaction.response.send_message("Durdurulmuş bir ses yok!", ephemeral=True)
          break
      else:
        await interaction.response.send_message("Bot sesi bulunamadı hatası, lütfen tekrar dene!", ephemeral=True)
        break
        
  else:
    await interaction.response.send_message("Bot ile aynı ses kanaılnda değilsin!", ephemeral=True)

@tree.command(name="çık", description="Ses Kanalından çıkar")
async def cik(interaction: discord.Interaction):
  self = interaction.client
  voices = self.voice_clients
  if voices is not None:
    voice = voices[0]
    await voice.disconnect(force=False)
    await interaction.response.send_message(
      f'{voice.channel} adlı kanaldan çıktım!')
  else:
    await interaction.response.send_message(f'Kanalda değilim galiba...')


@tree.command(
  name="çal",
  description="Youtubedan bir şey çalmanı sağlar (server gereksinimi yok)")
async def cal(interaction: discord.Interaction, mesaj: str):
  voices = interaction.client.voice_clients

  if not isinstance(interaction.user, discord.Member):  
    await interaction.response.send_message("Sesli kanala katılırken Bir Hata oluştu, lütfen tekrar deneyin",
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
    if interaction.user.voice.channel is None:
      await interaction.response.send_message("Ses Kanalında Değilsin.",
                                              ephemeral=True)
      return
    VoiceChannel = interaction.user.voice.channel
    voice = await VoiceChannel.connect()
  
  if not isinstance(voice, discord.VoiceClient):
    await interaction.response.send_message("Sese katılım hatası, lütfen tekrar deneyin",
                                            ephemeral=True)
    return
  
  await interaction.response.defer()
  # Get the search query from the message content
  # Create a YouTube downloader object
  with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      # Search for the video on YouTube
      yds = ydl.extract_info(f"ytsearch:{mesaj}", download=False)
      if yds is None:
        await interaction.followup.send("Youtube da bulunamadı lütfen tekrar dene!", ephemeral=True)
        return
      video_info = yds['entries'][0]
      # Get the audio stream from the video
      audio_url = video_info['url']
      # Create an audio source from the audio stream
      audio_source = discord.FFmpegPCMAudio(audio_url)
  # Play the audio in the voice channel
  voice.play(audio_source)
  embed = discord.Embed(title="Şarkı Çalınıyor", description=f"{video_info['title']}", color=0x00ff00)
  embed.set_thumbnail(url=video_info['thumbnail'])
  await interaction.followup.send(embed=embed, ephemeral=False)
  
    

@tree.command(name="neden", description="tüm sunucularda çalışması için test")
async def neden(interaction):
  await interaction.response.send_message("Kaplumbağa neden")


@tree.command(name="sustur", description="birini susturmanı sağlar")
async def sustur(interaction: discord.Interaction, user: discord.User):
  if not isinstance(user, discord.Member):
    await interaction.response.send_message("Kullanıcıyı bulamadım lütfen tekrar dene", ephemeral=True)
    return
  await user.edit(mute=True)
  await interaction.response.send_message(f"{user} susturuldu")


@tree.command(name="susturma_kaldır",
              description="Susturulmuş birinin susturmasını kapatmanı sağlar")
async def sustur_ac(interaction: discord.Interaction, kullanıcı: discord.User):
  if not isinstance(kullanıcı, discord.Member):
    await interaction.response.send_message("Kullanıcıyı bulamadım lütfen tekrar dene", ephemeral=True)
    return
  if kullanıcı.voice is None:
    await kullanıcı.edit(mute=False)
    await interaction.response.send_message(f"{kullanıcı} adlı kişinin sesi açıldı")
  else:
    await interaction.response.send_message(
      f"{kullanıcı} adlı kişi ses kanalında değil")


@tree.command(name="chatgpt",
              description="Botun gerçekten zeki olmasını sağlar")
async def chatgpt(interaction: discord.Interaction, mesaj: str):
  await interaction.response.defer(ephemeral=False)
  print("ChatGPT istek:", mesaj)
  response2 = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    temperature=1,
    messages=[
      {
        "role": "system",
        "content": "You are a general assistant named 'Herif bot' and you are in a discord server"
      },
      {
        "role": "user",
        "content": mesaj
      },
    ])
  if not isinstance(response2, dict):
    await interaction.followup.send(f"ChatGPT'den cevap alınamadı, lütfen tekrar dene. çalışmaz ise {kytpbs_tag} a bildir", ephemeral=True)
    return
  cevap = response2['choices'][0]['message']['content']
  embed = discord.Embed(title="ChatGPT", description=cevap)
  await interaction.followup.send(f"ChatGPT'den gelen cevap: \n ", embed=embed)

@tree.command(name="dogumgunu_ekle", description="Doğumgününü eklemeni sağlar")
async def dogumgunu(interaction: discord.Interaction, kullanıcı: discord.User, gun: str, ay: str, yıl: str):
  id = kullanıcı.id
  date = datetime(int(yıl), int(ay), int(gun))
  date_string = str(date.year) + "-" + str(date.month) + "-" + str(date.day)
  if id in birthdays and birthdays[id] is not None:
    await interaction.response.send_message(f"{kullanıcı.mention} adlı kişinin doğum günü zaten '{birthdays[id]}' olarak ayarlanmış " +
                                            f"Değiştirmek için lütfen {kytpbs_tag}'ya ulaşın", ephemeral=True)
    return
  birthdays[id] = date_string
  with open("birthdays.json", "w") as f:
    json.dump(birthdays, f)
  await interaction.response.send_message(f"{kullanıcı.mention} adlı kişinin doğum günü '{date_string}' olarak ayarlandı")


if token is not None:
  client.run(token)
else:
  raise Exception("Token bulunamadı")
