import discord
import time
import yt_dlp
from yt_dlp import YoutubeDL
from Read import readFile
import os
from datetime import datetime
from webserver import keep_alive
import random

ydl_opts = {
  'format': 'bestaudio/best',
  'keepvideo': False,
  'outtmpl': 'test.mp3',
}

sus_gif = "https://cdn.discordapp.com/attachments/726408854367371324/1010651691600838799/among-us-twerk.gif"

costom1 = readFile("Costom1.txt")
costom2 = readFile("Costom2.txt")
intents = discord.Intents.all()
intents.members = True
intents.voice_states = True
deleted_messsages_channel = 991442142679552131


class MyClient(discord.Client):

  async def on_ready(self):
    print('Logged on as', self.user)

  async def on_member_join(self, member):
    print(member, "Katıldı! ")
    channel = client.get_channel(929329231173910578)
    await channel.send("Salak bir kişi daha servera katıldı... Hoşgelmedin " +
                       member)

  async def on_member_remove(self, member):
    channel = client.get_channel(929329231173910578)
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
                                   color=696969)
    channel = discord.utils.get(client.get_all_channels(), name='boss-silinen')
    profile_change.set_image(url=pfp)
    await channel.send(embed=profile_change)

  async def on_member_ban(self, guild, user):
    channel = discord.utils.get(client.get_all_channels(), name='〖💬〗genel')
    await channel.send("Ah Lan " + str(user) + " Adlı kişi " + str(guild) +
                       " serverından banlandı ")
    print("Ah Lan", str(user), "Adlı kişi", str(guild), "serverından banlandı")

  async def on_member_unban(self, guild, user):
    try:
      await user.send("You are finally unbanned from " + str(guild) +
                      " Named server :)")
      print("sending dm to ..." + user + "Server: " + str(guild))
    except Exception:
      print("There were an error while sending a DM")
      channel = discord.utils.get(client.get_all_channels(), name='〖💬〗genel')
      await channel.send(
        f"{user} bu mal gibi {guild} sunucusuna geri girebilme hakkı kazanmılştır"
      )
      pass

  async def on_message_edit(self, before, message):
    if message.author == self.user:
      return
    embed = discord.Embed(
      title="Mesaj Düzenlendi",
      description=f"Kanal: {message.channel} \n Kişi: {message.author} \n"
      f"Eski Mesaj: {before.content} \n Yeni Mesaj: {message.content}",
      color=696969)
    channel = discord.utils.get(client.get_all_channels(), name='boss-silinen')
    await channel.send(embed=embed)

  async def on_message_delete(self, message):
    if message.author == self.user:
      return

    embed = discord.Embed(title="Mesaj silindi.",
                          description="Silinen Kanal: " +
                          str(message.channel) + "\n Silen Kişi: " +
                          str(message.author) + "\n Silinen Mesaj: " +
                          str(message.content),
                          color=696969)
    channel = discord.utils.get(client.get_all_channels(), name='boss-silinen')

    #image: (message.attachments[0].url)
    #print(image)
    #embed.set_image(url=image)
    await channel.send(embed=embed)

  async def on_message(self, message):
    x = message.content
    y = x.lower()
    user = message.author
    channel = message.channel
    guild = message.guild
    print(str(channel) + " " + str(user) + ": " + x)
    now = datetime.now()
    Time = now.strftime("%H:%M:")
    if message.author == self.user:
      return

    if Time == "09:11:":
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

    for i in range(len(costom1)):
      if x == costom1[i]:
        await message.reply(costom2[i])

    if 'tuna' in y:
      await message.channel.send("<@725318387198197861>")  #tuna tag

    if 'kaya' in y:
      await message.reply("Zeka Kübü")
      await message.channel.send("<@474944711358939170>")  #kaya tag

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
      embed = discord.Embed(title="Arraydekiler:", colour=696969)
      for i in range(len(costom1)):
        embed.add_field(name="Yazılan:", value=costom1[i], inline=True)
        embed.add_field(name="Cevaplar:", value=costom2[i] + "\n", inline=True)
      await message.reply(embed=embed)
    if y == "pfp":
      pfp = user.avatar_url
      embed = discord.Embed(title="Profile Foto Test",
                            description="profile: ",
                            type="rich",
                            color=696969)
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
      kanal = self.user.voice.channel
      await kanal.disconnect()
    if y == "rastgele katıl":
      kanallar = guild.voice_channels
      kanal = kanallar[randint(1,11)]
      kanal.connect()
    if y == "mi?":
      if self.voice_clients[0] is not None:
        self.voice_clients[0].play(discord.FFmpegPCMAudio("test.mp3"))
        await message.reply(f"{self.voice_clients[0]} dasın")
        print(f"{self.voice_clients[0]} dasın")
      else:
        await message.reply("Ses Kanalında Değilsin")

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
                            color=696969)
      embed.add_field(name="Söylenen: ", value=x.split(" ")[1], inline=True)
      embed.add_field(name="Botun cevabı: ",
                      value=x.split(" ")[2],
                      inline=True)
      await message.reply(embed=embed)
      print(f"1: {costom1} 2: {costom2}")

    if message.content.startswith("çal"):
      try:
        os.remove("test.mp3")
      except Exception:
        print("Dosya Yok")

      if len(x.split(",")) < 2:
        await message.reply('Virgül (",") Koyduğunuza Emin olun')
        return
      else:
        mesaj = x.split(",")[1]
      if "http" not in message.content:
        print("http yok")
        with YoutubeDL(ydl_opts) as ydl:
          yts = ydl.extract_info(f"ytsearch:{mesaj}",
                                 download=True)['entries'][0]
          await message.reply(f"Şarkı Çalınıyor: {yts['title']}")
          discord.FFmpegPCMAudio("test.mp3")
          print(mesaj)
      else:
        print("http var")
        mesaj = mesaj
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
          await message.reply("İndiriliyor Lütfen Bekleyin...")
          ydl.download([mesaj])
          await message.reply("İndirildi")
          await message.reply("Şarkı Çalınıyor")
          discord.FFmpegPCMAudio("test.mp3")

    if message.content.lower() == "dur":
      print("Dur Dendi")
      try:
        voice = self.voice_clients[0]
        await voice.stop()
        print("Durduruldu")
      except Exception:
        await message.reply("VC de değilim")

    if message.content.lower() == "devam":
      try:
        voice = self.voice_clients[0]
        await voice.resume()
        print("Tekrar Devam Edildi")
      except Exception:
        await message.reply("Ses Kanalında Değilsin")

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

keep_alive()
client = MyClient(intents=intents)
client.run(os.getenv('TOKEN'))
