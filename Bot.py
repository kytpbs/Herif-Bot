import discord
import time
import youtube_dl
import yt_dlp
from Read import readFile
import os
import Token

ydl_opts = {
    'format': 'bestaudio/best',
    'keepvideo': False,
    'outtmpl': 'test.mp3',
}

costom1 = []
costom2 = []
costom1 = readFile("Costom1.txt")
costom2 = readFile("Costom2.txt")
intents = discord.Intents.all()
intents.members = True
deleted_messsages_channel = 991442142679552131



class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_member_join(self, member):
        print(member, "Katıldı! ")
        channel = client.get_channel(929329231173910578)
        await channel.send("Salak bir kişi daha servera katıldı... Hoşgelmedin", member)

    async def on_member_remove(self, member):
        channel = client.get_channel(929329231173910578)
        await channel.send(
            "Zeki bir insan valrlığı olan " + "**" + str(member) + "**" + " Bu saçmalık serverdan ayrıldı")
        print(member, "Ayrıldı! ")

    async def on_guild_channel_create(self, channel):
        print("New Channel Created:", channel)
        if str(channel) == "a":
            await channel.send("Kanal 3 saniye içinde siliniyor")
            existing_channel = channel
            print("Deleting Channel " + str(channel) + "in 3 seconds")
            channel.send("Kanal 3 Saniye İçinde Siliniyor")
            for i in range(3):
                await channel.send(str(3 - i))
                time.sleep(1)
            await channel.send("Siliniyor...")
            await existing_channel.delete()

    async def on_user_update(self, before, after):
        pfp = before.avatar_url
        print("Profil değişti:", before)
        profile_change = discord.Embed(title="Biri profilini deiğiştirdi amk.",
                                       description="Eski Hali: " + str(before) + "\n Yeni Hali: " + str(after),
                                       color=696969)
        channel = discord.utils.get(client.get_all_channels(), name='boss-silinen')
        profile_change.set_image(url=pfp)
        await channel.send(embed=profile_change)

    async def on_member_ban(self, guild, user):
        channel = discord.utils.get(client.get_all_channels(), name='〖💬〗genel')
        await channel.send("Ah Lan " + str(user) + " Adlı kişi " + str(guild) + " serverından banlandı ")
        print("Ah Lan", str(user), "Adlı kişi", str(guild), "serverından banlandı")

    async def on_member_unban(self, guild, user):
        try:
            await user.send("You are finally unbanned from " + str(guild) + " Named server :)")
            print("sending dm to ..." + user + "Server: " + str(guild))
        except Exception:
            print("There were an error while sending a DM")
            channel = discord.utils.get(client.get_all_channels(), name='〖💬〗genel')
            await channel.send(f"{user} bu mal gibi {guild} sunucusuna geri girebilme hakkı kazanmılştır")
            pass

    async def on_message_edit(self, before, message):
        if message.author == self.user:
            return
        embed = discord.Embed(title="Mesaj Düzenlendi",
                              description=f"Kanal: {message.channel} \n Kişi: {message.author} \n"
                                          f"Eski Mesaj: {before.content} \n Yeni Mesaj: {message.content}",
                              color=696969)
        channel = discord.utils.get(client.get_all_channels(), name='boss-silinen')
        await channel.send(embed=embed)

    async def on_message_delete(self, message):
        if message.author == self.user:
            return

        embed = discord.Embed(title="Mesaj silindi.",
                              description="Silinen Kanal: " + str(message.channel) + "\n Silen Kişi: " + str(
                                  message.author) + "\n Silinen Mesaj: " + str(message.content), color=696969)
        channel = discord.utils.get(client.get_all_channels(), name='boss-silinen')
        await channel.send(embed=embed)

    async def on_message(self, message):
        x = message.content
        y = x.lower()
        user = message.author
        channel = message.channel
        guild = message.guild
        print(str(channel) + " " + str(user) + ": " + x)
        if message.author == self.user:
            return

        masaj = y.split(" ")
        masaj_uzunluk = len(masaj)
        son_mesaj = masaj[masaj_uzunluk - 1]
        if son_mesaj == ("nerde") or son_mesaj == ("nerede") or son_mesaj == ("neredesin") or son_mesaj == ("nerdesin"):
            print(son_mesaj)
            await message.reply(f'Ebenin amında. Ben sonu "{son_mesaj}" diye biten bütün mesajlara cevap vermek için kodlanmış bi botum. Seni kırdıysam özür dilerim.')

        for i in range (len(costom1)):
            if x == costom1[i]:
                await message.reply(costom2[i])

        if 'tuna' in y:
            await message.channel.send("<@725318387198197861>") #tuna tag

        if 'kaya' in y:
            await message.reply("Zeka Kübü")
            await message.channel.send("<@474944711358939170>") #kaya tag

        if 'neden' in y:
            await message.reply("Kaplumağa Deden :turtle: ")

        match y:
            case "ping":
                await message.reply("pong")
            case "31":
                await message.channel.send("sjsjsj")
            case "A":
                await message.reply(x)
            case "dm":
                await user.send("PING")
            case "sus":
                await message.reply("https://cdn.discordapp.com/attachments/726408854367371324/1010651691600838799/among-us-twerk.gif")
            case "cu":
                await message.reply("Ananın AMCUUUU")
            case "array":
                print(f"Array: {costom1}")
                embed = discord.Embed(title="Arraydekiler:", colour=696969)
                for i in range (len(costom1)):
                    embed.add_field(value=costom1[i], inline=True)
                    embed.add_field(name="cevaplar", value=costom2[i], inline=True)
                await message.reply(embed=embed)
            case "pfp":
                pfp = user.avatar_url
                embed = discord.Embed(title="Profile Foto Test", description="profile: ", type="rich", color=696969)
                embed.set_image(url=pfp)
                await message.channel.send(embed=embed)
            case "katıl":
                if user.voice is not None:
                    kanal = message.author.voice.channel
                    print(str(kanal) + "'a katılınıyor")
                    voice = await kanal.connect()
                if user.voice is None:
                    await message.channel.send("Bir Ses Kanalında Değilsin... Lütfen Tekrar Dene")
            case "çık:":
                kanal = self.user.voice.channel
                await kanal.disconnect()
            case "mi?":
                if self.voice_clients[0] is not None:
                    await message.reply(self.voice_clients[0] + "dasın")
                    print(f"{self.voice_clients[0]} dasın")
                else:
                    await message.reply("Ses Kanalında Değilsin")

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
            embed = discord.Embed(title="Yeni özel komut oluşturuldu:", description="Test: ", type="rich", color=696969)
            embed.add_field(name="Söylenen: ", value=x.split(" ")[1], inline=True)
            embed.add_field(name="Botun cevabı: ", value=x.split(" ")[2], inline=True)
            await message.reply(embed=embed)
            print(f"1: {costom1} 2: {costom2}")

        if message.content.startswith("çal"):
            try:
                voice = self.voice_clients[0]
                await voice.resume()
                print("Tekrar Devam Edildi")
            except Exception:
                pass
            try:
                os.remove("test.mp3")
            except Exception:
                print("Dosya Yok")
            try:
                mesaj = x.split(" ")[1]
            except Exception:
                await message.reply("Anlaşılamadı...")
                return
            video_info = youtube_dl.YoutubeDL().extract_info(
                url=mesaj, download=False)
            title = video_info['title']
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                await message.reply("İndiriliyor Lütfen Bekleyin...")
                ydl.download([mesaj])
            try:
                voice = self.voice_clients[0]
                await message.channel.send("Ses Kanalında")
                print("Ses Kanalında")
                voice.play(discord.FFmpegPCMAudio('test.mp3'))
                await message.reply("indirildi...")
                time.sleep(1)
                await message.reply(f"{title} adlı ses çalınıyor")
                return
            except Exception:
                if user.voice is not None:
                    await message.channel.send("Ses Kanalında Değil Katılma Eylemi...")
                    kanal = message.author.voice.channel
                    print(str(kanal) + "'a katılınıyor")
                    await message.reply(f"{str(kanal)} ' a katılınıyor")
                    voice = await kanal.connect()
                    voice.play(discord.FFmpegPCMAudio('test.mp3'))
                    await message.reply("indirildi...")
                    time.sleep(1)
                    await message.reply(f"{title} adlı ses çalınıyor")
                else:
                    await message.reply("Bir Ses Kanalında Değilsin")

        if message.content.lower() == "dur":
            print("Dur Dendi")
            try:
                voice = self.voice_clients[0]
                await voice.stop()
                print("Durduruldu")
            except Exception:
                await message.reply("VC de değilim")

        if y == "çık":
            try:
                voice = self.voice_clients[0]
                await voice.disconnect()
                print("Durduruldu")
            except Exception:
                await message.reply("VC de değilim")

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


client = MyClient(intents=intents)
client.run(Token.token)
