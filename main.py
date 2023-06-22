import json
import time
import discord
import yt_dlp
import os
import random
import openai
from Read import readFile, jsonRead, log
from datetime import datetime, time, timezone, tzinfo
from discord import app_commands
from discord.ext import tasks
from yt_dlp import YoutubeDL

ydl_opts = {
  'format': 'bestaudio',
  'noplaylist': True,
  'default_search': 'auto',
  'outtmpl': 'song.mp3',
  'keepvideo': False,
  'nooverwrites': False,
}


try:
  import Token
  token = Token.dev_token
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
deleted_messages_channel_id = 991442142679552131
general_chat_id = 1056268428308135976
birthday_role_id = 815183230789091328
kytpbs_tag = "<@474944711358939170>"
cyan = 0x00FFFF
cya = 696969

class MyClient(discord.Client):
  
  def __init__(self):
    super().__init__(intents=discord.Intents.all())
    self.deleted = False
    self.old_channel = None

  async def on_ready(self):
    await self.wait_until_ready()
    check_birthdays.start()
    await tree.sync()
    print('Logged on as', self.user)

  async def on_member_join(self, member: discord.Member):
    print(member, "Katıldı! ")
    general_channel = get_general_channel(member.guild)
    if isinstance(general_channel, discord.TextChannel):
      await general_channel.send(f"Zeki bir insan valrlığı olan {member.mention} Bu saçmalık {member.guild} serverına katıldı. Hoşgeldin!")

  async def on_member_remove(self, member):
    channel = get_general_channel(member.guild)
    if isinstance(channel, discord.TextChannel):
      await channel.send("Zeki bir insan valrlığı olan " + "**" + str(member) +
                        "**" + " Bu saçmalık serverdan ayrıldı")
    print(member, "Ayrıldı! ")

  async def on_guild_channel_create(self, channel):
    print(channel, "Oluşturuldu")
    deleted_messages_channel = self.get_channel(deleted_messages_channel_id)
    if isinstance(deleted_messages_channel, discord.TextChannel):
      await deleted_messages_channel.send(
        f"**{channel}** adlı kanal oluşturuldu")
  
  async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
    print(channel, "Silindi")
    deleted_messages_channel = self.get_channel(deleted_messages_channel_id)
    if isinstance(deleted_messages_channel, discord.TextChannel):
      message = await deleted_messages_channel.send(
        f"**{channel}** adlı kanal silindi geri oluşturmak için reaksiyon verin (içindeki yazı kurtarılamıyor, sadece son silinen kanal kurtarılabilir)")
      await message.add_reaction("🔙")
      self.old_channel = channel
      self.deleted = True

  async def on_reaction_add(self, reaction: discord.Reaction, user):
    print(reaction.emoji, "Eklendi")
    if reaction.emoji == "🔙":
      if self.old_channel is None:
        await reaction.message.channel.send("Silinen Kanal bulunamadı")
        return
      if self.deleted:
        if isinstance(user, discord.Member) and not user.guild_permissions.administrator:
          await reaction.message.channel.send("Bu kanalı geri oluşturmak için yetkiniz yok")
          return
        new_channel = await self.old_channel.clone(reason="Kanal geri oluşturuldu")
        self.deleted = False
        await reaction.message.channel.send(f"{new_channel.mention} adlı kanal geri oluşturuldu")
        await reaction.message.delete(delay=1)
        return

  async def on_member_update(self, before: discord.Member, after: discord.Member):
    pfp = before.avatar_url # type: ignore
    print("Profil değişti:", before)
    profile_change = discord.Embed(title="Biri profilini deiğiştirdi amk.",
                                   description="Eski Hali: " + str(before) +
                                   "\n Yeni Hali: " + str(after),
                                   color=cya)
    channel = self.get_channel(deleted_messages_channel_id)
    profile_change.set_image(url=pfp)
    if isinstance(channel, discord.TextChannel):
      await channel.send(embed=profile_change)

  async def on_member_ban(self, guild: discord.Guild, user):
    channel = self.get_channel(general_chat_id)
    if isinstance(channel, discord.TextChannel):
      await channel.send("Ah Lan " + str(user) + " Adlı kişi " + str(guild) +
                        " serverından banlandı ")
      return
    raise RuntimeError(f"Kanal Bulunamadı: aranan id: {general_chat_id}")

  async def on_member_unban(self, guild: discord.Guild, user: discord.User):
    try:
      await user.send("You are finally unbanned from " + str(guild) +
                      " Named server :)")
      print(f"{user} unbanned from {guild}, sending a DM")
    except Exception:
      print(f"There were an error while sending a DM about unban to {user} from {guild}")
      
      channel = self.get_channel(general_chat_id)
      if isinstance(channel, discord.TextChannel):
        await channel.send(
          f"{user.name} bu mal gibi {guild.name} sunucusuna geri girebilme hakkı kazanmılştır"
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

    channel = self.get_channel(deleted_messages_channel_id)
    if isinstance(channel, discord.TextChannel):
        await channel.send(embed=embed)

  async def on_message_delete(self, message):
    if message.author == self.user:
      return
    
    channel = self.get_channel(deleted_messages_channel_id)
    
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
      embeds2 = None
    if isinstance(channel, discord.TextChannel) and embeds2 is not None:
      await channel.send(embeds=embeds2)

  async def on_message(self, message):
    Message_Content = message.content
    Message_Content_Lower = Message_Content.lower()
    user = message.author
    channel = message.channel
    guild = message.guild


    Time = datetime.now().strftime("%H:%M:")
    if guild is None:
      guild = "DM"
    data = f'{str(Time)} {str(guild)} {str(channel)} {str(user.name)}: {str(Message_Content)}'
    print(data)
    if message.embeds is None:
      log(str(data))

    if message.author == self.user:
      return
    
    

    if isinstance(channel, discord.DMChannel):
      #is response to a message
      if message.reference is not None:
        print(f"Message is a response to a message that is {message.reference.resolved.content}")
        await message.reply(gpt(Message_Content, "You are in a DM channel", message.reference.resolved.content)['content'])
      else:
        await message.reply(gpt(Message_Content, "You are in a DM channel")['content'])

    if Time == "06:11:":  #9:11 for +3 timezone
      await channel.send("🛫🛬💥🏢🏢")
    
    masaj = Message_Content_Lower.split(" ")
    masaj_uzunluk = len(masaj)
    son_mesaj = masaj[masaj_uzunluk - 1]
    if son_mesaj == ("nerde") or son_mesaj == ("nerede") or son_mesaj == (
        "neredesin") or son_mesaj == ("nerdesin"):
      print(son_mesaj)
      await message.reply(
        f'Ebenin amında. Ben sonu "{son_mesaj}" diye biten bütün mesajlara cevap vermek için kodlanmış bi botum. Seni kırdıysam özür dilerim.'
      )

    for i in range(1, len(costom1)):
      if Message_Content == costom1[i]:
        await message.reply(costom2[i])

    if 'tuna' in Message_Content_Lower:
      await message.channel.send("<@725318387198197861>")  # tuna tag

    if 'kaya' in Message_Content_Lower:
      await message.reply("Zeka Kübü")
      await message.channel.send("<@474944711358939170>")  # kaya tag

    if 'neden' in Message_Content_Lower:
      await message.reply("Kaplumağa Deden :turtle: ")

    if Message_Content_Lower == "ping":
      await message.reply(f"PONG, ping: {round(self.latency * 1000)}ms")
    
    if Message_Content_Lower == "31":
      await message.channel.send("sjsjsj")
   
    if Message_Content_Lower == "A":
      await message.reply(Message_Content)
    
    if Message_Content_Lower == "dm":
      await user.send("PING")
    
    if Message_Content_Lower == "sus":
      await message.reply(sus_gif)
    
    if Message_Content_Lower == "cu":
      await message.reply("Ananın AMCUUUU")

    if Message_Content_Lower == "array":
      print(f"Array: {costom1}")
      embed = discord.Embed(title="Arraydekiler:", colour=cya)
      for i in range(len(costom1)):
        embed.add_field(name="Yazılan:", value=costom1[i], inline=True)
        embed.add_field(name="Cevaplar:", value=costom2[i] + "\n", inline=True)
      await message.reply(embed=embed)
    
    if Message_Content_Lower == "pfp":
      pfp = user.avatar_url
      embed = discord.Embed(title="Profile Foto Test",
                            description="profile: ",
                            type="rich",
                            color=cya)
      embed.set_image(url=pfp)
      await message.channel.send(embed=embed)
    
    if Message_Content_Lower == "katıl":
      if user.voice is not None:
        kanal = message.author.voice.channel
        print(str(kanal) + "'a katılınıyor")
        await kanal.connect()
      if user.voice is None:
        await message.channel.send(
          "Bir Ses Kanalında Değilsin... Lütfen Tekrar Dene")
    
    if Message_Content_Lower == "çık:":
      if self.voice_clients and self.voice_clients[0]:
        kanal = self.voice_clients[0].channel
        if isinstance(kanal, discord.VoiceProtocol):
          await kanal.disconnect(force=False)
    
    if Message_Content_Lower == "rastgele katıl":
      if not isinstance(guild , discord.Guild):
        await message.reply("Bir hata oluştu, lütfen tekrar deneyin")
        return
      if (len(guild.voice_channels) == 0):
        await message.reply("Sunucuda ses kanalı bulunamadı")
        return
      
      kanallar = guild.voice_channels
      kanal = kanallar[random.randint(1, 11)]
      await kanal.connect()

    if Message_Content_Lower == "söyle":
      if masaj_uzunluk > 1:
        await message.channel.send(masaj[1])
      else:
        await message.reply("Ne söyleyeyim?")

    if message.content.startswith("oluştur"):
      print("oluştur")
      if len(Message_Content.split(" ")) < 2:
        await message.reply("İlk Mesajı girmediniz.")
        return
      if len(Message_Content.split(" ")) < 3:
        await message.reply("Son Mesajı Girmediniz")
        return
      print(f"uzunluklar: 1: {len(costom1)} 2:")
      x1 = ['', Message_Content.split(" ")[1]]
      x2 = ['', Message_Content.split(" ")[2]]
      costom1.append(Message_Content.split(" ")[1])
      costom2.append(Message_Content.split(" ")[2])
      with open('Costom1.txt', 'a') as f:
        f.writelines('\n'.join(x1))
      with open('Costom2.txt', 'a') as l:
        l.writelines('\n'.join(x2))
      embed = discord.Embed(title="Yeni özel komut oluşturuldu:",
                            description="Test: ",
                            type="rich",
                            color=cya)
      embed.add_field(name="Söylenen: ", value=Message_Content.split(" ")[1], inline=True)
      embed.add_field(name="Botun cevabı: ",
                      value=Message_Content.split(" ")[2],
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
        await message.reply(Message_Content.split(" ")[1])

client = MyClient()
tree = app_commands.CommandTree(client)

def get_general_channel(guild: discord.Guild):
  for channel in guild.text_channels:
    if "genel" in channel.name.lower() or "general" in channel.name.lower():
      return channel
  return None

def get_user_and_date_from_string(dict: dict):
  new_dict = {}
  for user_id, date in dict.items():
    user = client.get_user(int(user_id))
    if user is None:
      continue
    dates = date.split("-")
    if len(dates) != 3:
      e = ValueError("Hatalı tarih formatı, lütfen düzeltin!")
      print(e)
      continue
    date_obj = datetime(int(dates[0]), int(dates[1]), int(dates[2]))
    print(f"{user} : {date_obj}")
    if date_obj is None:
      continue
    new_dict[user] = date_obj

  return new_dict

async def get_voice(interaction: discord.Interaction):
  voices = interaction.client.voice_clients
  
  if not isinstance(interaction.user, discord.Member):  
    await interaction.response.send_message("Sesli kanala katılırken Bir Hata oluştu, lütfen tekrar deneyin. " +
                                            "Hata: Kullanıcı bulunamadı", ephemeral=True)
    raise ValueError("Kullanıcı bulunamadı")
  
  if not isinstance(interaction.guild, discord.Guild):
    await interaction.response.send_message("Youtubedan çalma sadece sunucularda çalışır." +
                                            "Hata: Sunucu bulunamadı", ephemeral=True)
    raise ValueError("Sunucu bulunamadı")
  
  if interaction.user.voice is None:
    await interaction.response.send_message("Ses Kanalında Değilsin. hata: 'ses bulunamadı'",
                                            ephemeral=True)
    raise ValueError("Ses bulunamadı")

  if interaction.user.voice.channel is None:
    await interaction.response.send_message("Ses Kanalında Değilsin. hata: 'kanal bulunamadı'",
                                            ephemeral=True)
    return
  for i in voices:
    if not isinstance(i, discord.VoiceClient):
      print(Warning("Listede Olmaması Gereken Bir Şey Var"))
      continue
    
    if i.channel == interaction.user.voice.channel:
      if i.is_playing():
        await interaction.response.send_message("Bot zaten çalıyor. lütfen bitmesini bekle.", ephemeral=True)
        return
      voice = i
      break
    
    if i.guild == interaction.guild:
      if not i.is_playing():
        await i.disconnect(force=True)
        voice = await interaction.user.voice.channel.connect()
        break
      
      await interaction.response.send_message("Bot başka bir ses kanalında zaten çalıyor lütfen bitmesini bekle.", ephemeral=True)
    
  else:
    VoiceChannel = interaction.user.voice.channel
    voice = await VoiceChannel.connect()
  
  if not isinstance(voice, discord.VoiceClient):
    await interaction.response.send_message("Sese katılım hatası, lütfen tekrar deneyin",
                                            ephemeral=True)
    raise RuntimeError("Sese katılım hatası")
  return voice

@tasks.loop(time= time(hour=6,minute=30, tzinfo=timezone.utc)) #9.30 for +3 timezone
async def check_birthdays():
  genel = client.get_channel(general_chat_id)
  if not isinstance(genel, discord.TextChannel):
    raise ValueError(f"Kanal Bulunamadı aranan id: {general_chat_id}")
  rol = genel.guild.get_role(birthday_role_id)
  today = datetime.now()
  usuable_dict = get_user_and_date_from_string(birthdays)
  
  if not isinstance(rol, discord.Role):
    raise RuntimeError(f"Rol Bulunamadı aranan id: {birthday_role_id}")
  if not isinstance(genel, discord.TextChannel):
    raise RuntimeError(f"Kanal Bulunamadı aranan id: {general_chat_id}")
  
  # remove birthday role from members that have it.
  for member in client.get_all_members():
    if member.get_role(birthday_role_id) is not None:
      print(f"{member} adlı kişinin doğum günü rolü kaldırılıyor")
      await member.remove_roles(rol)

  for user, birthday in usuable_dict.items():
    if birthday.month == today.month and birthday.day == today.day:
        age = today.year - birthday.year
        await user.add_roles(rol) # add birthday role to user.
        await genel.send(f"{user.mention} {age} yaşına girdi. Doğum günün kutlu olsun!")

@tree.command(name="sa", description="Bunu kullanman sana 'as' der")
async def self(interaction: discord.Interaction):
  await interaction.response.send_message(f"as, ping: {round(client.latency * 1000)}ms")


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

@tree.command(name="kanala_katıl",
              description="sunucuda rastgele bir kanala katılır")
async def channel_join(interaction: discord.Interaction, channel: discord.VoiceChannel = None):
  if channel is not None:
    await channel.connect()
    await interaction.response.send_message(f'"{channel}" adlı kanala katıldım!')
    return
  
  kanallar = interaction.guild.voice_channels
  kanal = kanallar[random.randint(1, len(kanallar) - 1)]
  await kanal.connect()
  await interaction.response.send_message(f'"{kanal}" adlı kanala katıldım!')

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
async def cik(interaction: discord.Interaction, zorla: bool = False):
  self = interaction.client
  voices = self.voice_clients

  if not isinstance(interaction.user, discord.Member):
      await interaction.response.send_message("Bir kullanıcı değilsin hatası, lütfen tekrar deneyin",
                                              ephemeral=True)
      print(Warning("Bir Kullanıcı Değil"))
      return
  
  if not isinstance(interaction.user.voice, discord.VoiceState):
    await interaction.response.send_message("Ses Kanalında Değilsin.",
                                            ephemeral=True)
    return
  
  for i in voices:
    if not isinstance(i, discord.VoiceClient):
      print(Warning("Listede Olmaması Gereken Bir Şey Var"))
      continue
    
    if i.channel == interaction.user.voice.channel:
      if i.is_playing() and not zorla:
        await interaction.response.send_message("Bot başka bir ses kanalında zaten çalıyor lütfen bitmesini bekle. yönetici isen zorla yap", ephemeral=True)
        return
      if i.is_playing() and zorla:
        i.stop()
      await i.disconnect()
      await interaction.response.send_message(f"{i.channel} adlı kanaldan çıktım")
      break

    if i.guild == interaction.guild:
      if zorla:
        if i.is_playing():
          i.stop()
        await i.disconnect()
        await interaction.response.send_message(f"{i.channel} adlı kanaldan çıktım")
        break
      
      if interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Botla aynı kanalda değilsin, zorla kullanarak çıkabilirsin", ephemeral=True)
        break
      
      await interaction.response.send_message("Bot ile aynı kanalda değilsin", ephemeral=True)

  else:
    await interaction.response.send_message(f'Seninle Aynı Kanalda değilim galiba...')


@tree.command(name="çal",
  description="Youtubedan bir şey çalmanı sağlar (yeni!)")
async def cal(interaction: discord.Interaction, mesaj: str, zorla: bool = False):
  voices = interaction.client.voice_clients
  
  if not isinstance(interaction.user, discord.Member):  
    await interaction.response.send_message("Sesli kanala katılırken Bir Hata oluştu, lütfen tekrar deneyin. " +
                                            "Hata: Kullanıcı bulunamadı", ephemeral=True)
    return
  
  if zorla and not interaction.user.guild_permissions.administrator:
    await interaction.response.send_message("Bu komutu zorla kullanmak için yönetici olmalısın.",
                                            ephemeral=True)
    return
  
  if not isinstance(interaction.guild, discord.Guild):
    await interaction.response.send_message("Youtubedan çalma sadece sunucularda çalışır." +
                                            "Hata: Sunucu bulunamadı", ephemeral=True)
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
      print(Warning("Listede Olmaması Gereken Bir Şey Var"))
      continue

    if i.channel == interaction.user.voice.channel:
      if i.is_playing():
        if zorla:
          i.stop()
          voice = i
          break
        if interaction.user.guild_permissions.administrator:
          await interaction.response.send_message("Bot zaten çalıyor. zorla yaparak değiştirebilirsin", ephemeral=True)
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
        await interaction.response.send_message("Bot başka bir ses kanalında zaten çalıyor lütfen bitmesini bekle.", ephemeral=True)
        return
    
  else:
    VoiceChannel = interaction.user.voice.channel
    voice = await VoiceChannel.connect()
  
  if not isinstance(voice, discord.VoiceClient):
    await interaction.response.send_message("Sese katılım hatası, lütfen tekrar deneyin",
                                            ephemeral=True)
    return
  
  await interaction.response.defer()
  # Get the search query from the message content
  # Download Music
  with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      # Search for the video on YouTube
      sent_message = await interaction.followup.send(f"{mesaj} Youtube da aranıyor lütfen bekleyin...", ephemeral=False, wait=True)
      yds = ydl.extract_info(f"ytsearch:{mesaj}", download=True)
      if yds is None:
        await interaction.followup.send("Youtube da bulunamadı lütfen tekrar dene!", ephemeral=True)
        return
      video_info = yds['entries'][0]
 
  # Play the audio in the voice channel
  audio_source = discord.FFmpegPCMAudio('song.mp3')
  voice.play(audio_source)
  embed = discord.Embed(title="Şarkı Çalınıyor", description=f"{video_info['title']}", color=0x00ff00)
  embed.set_thumbnail(url=video_info['thumbnail'])
  await sent_message.edit(content="",embed=embed)

@tree.command(name="neden", description="komke")
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
  cevap = gpt(mesaj, use_function=True)[['content']]
  print(f"Cevap: {cevap}")
  if cevap.get("function_call"):
    function_name = cevap['function_call']['name']
  if cevap == -1:
    await interaction.followup.send("Bir hata oluştu, lütfen tekrar deneyin", ephemeral=True)
    return
  embed = discord.Embed(title="ChatGPT", description=cevap)
  await interaction.followup.send(f"ChatGPT'den gelen cevap: \n ", embed=embed)

@tree.command(name="foto", description="Bir Fotoğraf Oluşturmanı Sağlar")
async def foto(interaction: discord.Interaction, mesaj: str):
  await interaction.response.defer(ephemeral=False)
  embed = discord.Embed(title="Foto", description=f'"{mesaj}" için oluşturulan fotoğraf: ')
  embeds = []
  embeds.append(embed)
  try:
    image = openai.Image.create(prompt=mesaj, n=1)
    if image is not None:
      images = image["data"]
      image_url = image["data"][0]["url"]
      embed.set_image(url=image_url)
  except openai.InvalidRequestError:
    embed = discord.Embed(title="HATA", description="+18 olduğu için izin verilmedi (kapatılamıyor)")
    return
  except openai.OpenAIError:
    embed = discord.Embed(title="HATA", description="Bir hata oluştu, hata: 'OpenAIError'")
    return
  except Exception as e:
    embed = discord.Embed(title="HATA", description=f"Bir hata oluştu: {e.__class__.__name__}")
    return
  if image is None:
    embed = discord.Embed(title="HATA", description="Bir hata oluştu: 'image bulunamadı'")
    return
  for index, url in enumerate(images):
    embeds.append(discord.Embed(title=f"Fotoğraf {index + 1}",url=url["url"]))
  await interaction.followup.send(embeds=embeds, ephemeral=False)

@tree.command(name="dogumgunu_ekle", description="Doğumgününü eklemeni sağlar")
async def dogumgunu_ekle(interaction: discord.Interaction, kullanıcı: discord.User, gun: str, ay: str, yıl: str):
  id = kullanıcı.id
  date = datetime(int(yıl), int(ay), int(gun))
  date_string = str(date.year) + "-" + str(date.month) + "-" + str(date.day)
  if id in birthdays and birthdays[str(id)] is not None:
    await interaction.response.send_message(f"{kullanıcı.mention} adlı kişinin doğum günü zaten '{birthdays[str(id)]}' olarak ayarlanmış " +
                                            f"Değiştirmek için lütfen {kytpbs_tag}'ya ulaşın", ephemeral=True)
    return
  birthdays[str(id)] = date_string
  with open("birthdays.json", "w") as f:
    json.dump(birthdays, f)
  await interaction.response.send_message(f"{kullanıcı.mention} adlı kişinin doğum günü '{date_string}' olarak ayarlandı")

@tree.command(name="dogumgunu_sil", description="Doğumgününü silmeni sağlar eğer mod değilsen başkasının doğum gününü silemezsin")
async def dogumgunu_sil(interaction: discord.Interaction, kullanıcı: discord.User):
  
  if not isinstance(interaction.user, discord.Member):
    await interaction.response.send_message("Bir hata oluştu, lütfen tekrar deneyin",
                                            ephemeral=True)
    return
  
  if interaction.user != kullanıcı and interaction.user.get_role(763458533819285556) is None:
    await interaction.response.send_message("Sadece Kendi Doğumgününü Silebilirsin", ephemeral=True)
    return
  id = str(kullanıcı.id)
  if id in birthdays and birthdays[id] is not None:
    birthdays.pop(id)
    with open("birthdays.json", "w") as f:
      json.dump(birthdays, f)
    await interaction.response.send_message(f"{kullanıcı.mention} adlı kişinin doğum günü silindi")
  else:
    await interaction.response.send_message(f"{kullanıcı.mention} adlı kişinin doğum günü zaten kayıtlı değil", ephemeral=True)

@tree.command(name="dogumgunu_goster", description="Kişinin doğumgününü gösterir")
async def dogumgunu_goster(interaction: discord.Interaction, kullanıcı: discord.User):
  id = str(kullanıcı.id)
  if id in birthdays and birthdays[id] is not None:
    await interaction.response.send_message(f"{kullanıcı.mention} adlı kişinin doğum günü '{birthdays[id]}'")
  else:
    await interaction.response.send_message(f"{kullanıcı.mention} adlı kişinin doğum günü kayıtlı değil", ephemeral=True)

@tree.command(name="dogumgunu_listele", description="Doğumgünlerini listeler, sadece modlar kullanabilir")
async def dogumgunu_listele(interaction: discord.Interaction):
  if not isinstance(interaction.user, discord.Member):
    await interaction.response.send_message("Bir hata oluştu, lütfen tekrar deneyin", ephemeral=True)
    return
  
  if interaction.user.guild_permissions.administrator is False:
    await interaction.response.send_message("Bu komutu kullanmak için gerekli iznin yok", ephemeral=True)
    return
  
  embed = discord.Embed(title="Doğumgünleri", description="Doğumgünleri", color=cyan)
  new_list = get_user_and_date_from_string(birthdays)
  for user, date in new_list.items():
    embed.add_field(name=f"{user}:", value=f"{date}", inline=False)
  await interaction.response.send_message(embed=embed)

# content: extra content to add
def gpt(mesaj, content="", refrence=None, use_function=False):
  messages=[
  {
    "role": "system",
    "content": "You are a general assistant named 'Herif bot' and you are in a discord server" + f"{content}",
  },
  {
    "role": "user",
    "content": mesaj,
  },
  ]
  functions = None
  if use_function:
    functions = [
      {
        "name": "play_youtube",
        "description": "a void function that plays a youtube video",
        "parameters": {
          "type": "object",
          "properties": {
            "title": {
              "type": "string",
              "description": "the title of the video to play, e.g. 'Never gonna give you up'",
            },
            "volume": {
              "type": "number",
              "description": "the volume to play the video at, e.g. 50",
            }
          },
          "required": ["title"],
        },
      },
    ]
  if refrence is not None:
    messages.append({
      "role": "assistant",
      "content": refrence
    })
  response2 = openai.ChatCompletion.create(
    model="gpt-3.5-turbo-0613",
    temperature=1,
    messages=messages,
  )
    
  if not isinstance(response2, dict):
    return -1;
  cevap = response2['choices'][0]['message']
  return cevap

def play_youtube(title: str):
  print("playing " + title)
if token is not None:
  client.run(token)
else:
  raise ValueError("Token bulunamadı")
