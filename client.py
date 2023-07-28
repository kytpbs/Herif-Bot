import random
from datetime import datetime

import discord

import GPT
from Constants import CYAN, DELETED_MESSAGES_CHANNEL_ID, GENERAL_CHAT_ID
from Read import json_read
from Tasks import start_tasks
from helper_functions import get_general_channel
from logging_system import log, DEBUG

custom_responses = json_read('responses.json')
birthdays = json_read('birthdays.json')


# noinspection PyMethodMayBeStatic
class MyClient(discord.Client):

  def __init__(self):
    super().__init__(intents=discord.Intents.all())
    self.deleted = False
    self.synced = False
    self.old_channel = None

  async def on_ready(self):
    await self.wait_until_ready()
    import Commands
    tree = Commands.get_tree_instance()
    if not self.synced:
      await tree.sync()
      start_tasks()
      self.synced = True
    print('Logged on as', self.user)
    log(f"Logged on as {self.user}", level=DEBUG)

  async def on_member_join(self, member: discord.Member):
    print(member.name, "Katıldı! ")
    log(f"{member.name}, joined {member.guild.name}", level=DEBUG)
    general_channel = get_general_channel(member.guild)
    if isinstance(general_channel, discord.TextChannel):
      await general_channel.send(
        f"Zeki bir insan valrlığı olan {member.mention} Bu saçmalık {member.guild} serverına katıldı. Hoşgeldin!")

  async def on_member_remove(self, member: discord.Member):
    log(f"{member.name}, left {member.guild.name}", DEBUG)
    channel = get_general_channel(member.guild)
    if isinstance(channel, discord.TextChannel):
      await channel.send("Zeki bir insan valrlığı olan " + "**" + str(member) +
                         "**" + " Bu saçmalık serverdan ayrıldı")
    print(member, "Ayrıldı! ")

  async def on_guild_channel_create(self, channel):
    print(channel, "Oluşturuldu")
    log(f"At {channel.guild.name}, {channel} was created.", DEBUG)

    deleted_messages_channel = self.get_channel(DELETED_MESSAGES_CHANNEL_ID)
    if isinstance(deleted_messages_channel, discord.TextChannel):
      await deleted_messages_channel.send(
        f"**{channel}** adlı kanal oluşturuldu")

  async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
    log(f"At {channel.guild.name}, {channel} was deleted.", DEBUG)
    deleted_messages_channel = self.get_channel(DELETED_MESSAGES_CHANNEL_ID)
    if isinstance(deleted_messages_channel, discord.TextChannel):
      message = await deleted_messages_channel.send(
        f"**{channel}** adlı kanal silindi geri oluşturmak için reaksiyon verin (içindeki yazı kurtarılamıyor, sadece son silinen kanal kurtarılabilir)")
      await message.add_reaction("🔙")
      self.old_channel = channel
      self.deleted = True

  async def on_reaction_add(self, reaction: discord.Reaction, user):

    log(f"{user.name} reacted with {reaction.emoji} to {reaction.message.content}", DEBUG)
    if user == self.user:
      return
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
    embed = discord.Embed(title="Biri profilini deiğiştirdi amk.", description=after.mention, color=CYAN)

    if before.nick != after.nick:
      log(f"{before.name}'s nickname changed from {before.nick} to {after.nick}", DEBUG)
      embed.add_field(name="Eski Nick:", value=before.nick, inline=False)
      embed.add_field(name="Yeni Nick:", value=after.nick, inline=False)

    if before.avatar != after.avatar:
      log(f"{before.name}'s profile picture changed.", DEBUG)

      if before.avatar is None:
        embed.add_field(name="Eski Profil Fotoğrafı:", value="Yok", inline=False)
      else:
        if after.avatar is None:
          embed.set_thumbnail(url=before.avatar.url)
        else:
          embed.add_field(name="Eski Profil Fotoğrafı:", value=before.avatar.url, inline=False)
      if after.avatar is None:
        embed.add_field(name="Yeni Profil Fotoğrafı:", value="Yok", inline=False)
      else:
        embed.set_thumbnail(url=after.avatar.url)

    if before.roles != after.roles:
      log(f"{before.name}'s roles changed.", DEBUG)

      for role in before.roles:
        if role not in after.roles:
          embed.add_field(name="Rol Silindi:", value=role.mention, inline=False)

      for role in after.roles:
        if role not in before.roles:
          embed.add_field(name="Rol Eklendi:", value=role.mention, inline=False)

    if before.status != after.status:
      log(f"{before.name}'s status changed from {before.status} to {after.status}", DEBUG)
      embed.add_field(name="Eski Durum:", value=before.status, inline=False)
      embed.add_field(name="Yeni Durum:", value=after.status, inline=False)

    channel = self.get_channel(DELETED_MESSAGES_CHANNEL_ID)
    if isinstance(channel, discord.TextChannel):
      await channel.send(embed=embed)

  async def on_member_ban(self, guild: discord.Guild, user: discord.Member):
    channel = get_general_channel(guild)
    log(f"{user.name} was banned from {guild.name}", DEBUG)
    if isinstance(channel, discord.TextChannel):
      await channel.send("Ah Lan " + str(user) + " Adlı kişi " + str(guild) +
                         " serverından banlandı ")
      return
    raise RuntimeError(f"Kanal Bulunamadı: aranan id: {GENERAL_CHAT_ID}")

  async def on_member_unban(self, guild: discord.Guild, user: discord.User):
    log(f"{user.name} was unbanned from {guild.name}", DEBUG)
    invite = await guild.text_channels[0].create_invite(target_user=user,
                                                        reason="Ban kaldırıldı, sunucuya geri davet ediliyor", max_uses=1)
    try:
      await user.send(f"artık {guild.name} sunucusuna geri girebilirsin. giriş linkin: {invite}")
    except discord.Forbidden:
      log(f"Couldn't send message to {user.name}")
    channel = self.get_channel(GENERAL_CHAT_ID)
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

    embed = discord.Embed(title="Mesaj Düzenlendi", description="Biri Mesajını Düzenlendi", color=CYAN)

    embed.add_field(name="Kanal: ", value=message.channel, inline=False)
    embed.add_field(name="Kişi: ", value=message.author, inline=False)
    embed.add_field(name="Eski Mesaj: ", value=before.content, inline=False)
    embed.add_field(name="Yeni Mesaj: ", value=message.content, inline=False)

    channel = self.get_channel(DELETED_MESSAGES_CHANNEL_ID)
    if isinstance(channel, discord.TextChannel):
      await channel.send(embed=embed)

  async def on_message_delete(self, message: discord.Message):
    if message.author == self.user:
      return

    channel = self.get_channel(DELETED_MESSAGES_CHANNEL_ID)

    if message.guild is not None:
      async for entry in message.guild.audit_logs(
        action=discord.AuditLogAction.message_delete):
        print(f'{entry.user} deleted {entry.target} at {entry.created_at}')
        who_deleted = entry.user
        break
      else:
        who_deleted = None
    else:
      who_deleted = None
    embed = discord.Embed(
      title="Mesaj silindi.", description="Silinen Mesaj: " + str(message.content),
      color=CYAN)

    embed.add_field(name="Silinen kanal:", value=message.channel, inline=False)
    embed.add_field(name="Gönderen kişi:", value=message.author, inline=False)

    if who_deleted is not None:
      embed.add_field(name="Silen kişi:", value=who_deleted, inline=False)

    if message.attachments is not None:
      if len(message.attachments) == 1:
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

  async def on_message(self, message: discord.Message):
    message_content = message.content
    message_content_lower = message_content.lower()
    user = message.author
    channel = message.channel
    guild = message.guild

    time = datetime.now().strftime("%H:%M:")
    if guild is None:
      guild = "DM"
    data = f'{str(time)} {str(guild)} {str(channel)} {str(user.name)}: {str(message_content)}'
    print(data)
    if message.embeds is None:
      log(data)

    if message.author == self.user:
      return

    if custom_responses.get(message_content) is not None:
      await message.reply(custom_responses[message.content])

    if isinstance(channel, discord.DMChannel):
      if message.reference is not None and message.reference.resolved is not None and not isinstance(
        message.reference.resolved, discord.DeletedReferencedMessage):  # is responding to a message

        reference = message.reference.resolved
        if reference.reference is None or reference.reference.resolved is None or isinstance(reference.reference.resolved, discord.DeletedReferencedMessage):
          messages_dict = {"Missing": message.reference.resolved.content}
        else:
          messages_dict = {reference.reference.resolved.content: message.reference.resolved.content}
        print(f"Message is a response to a message that is {message.reference.resolved.content}")
        async with message.channel.typing():
          answer = GPT.chat(messages_dict, message.content, dont_send_token_usage=True)
        if not isinstance(answer, int):
          await message.reply(answer['content'])
        else:
          await message.reply("Botta bir hata oluştu, Lütfen tekrar dene")
      else:
        answer = GPT.question("You are talking on a dm channel!" + message_content, message.author.name)
        if answer != -1:
          await message.reply(str(answer))
        else:
          await message.reply("Botta bir hata oluştu, Lütfen tekrar dene!")

    if time == "06:11:":  # 9:11 for +3 timezone
      await channel.send("🛫🛬💥🏢🏢")

    son_mesaj = message.content.lower().split(" ")[-1]
    if son_mesaj == "nerde" or son_mesaj == "nerede" or son_mesaj == (
      "neredesin") or son_mesaj == "nerdesin":
      print(son_mesaj)
      await message.reply(
        f'Ebenin amında. Ben sonu "{son_mesaj}" diye biten bütün mesajlara cevap vermek için kodlanmış bi botum. Seni kırdıysam özür dilerim.'
      )

    if 'tuna' in message_content_lower:
      await message.channel.send("<@725318387198197861>")  # tuna tag

    if 'kaya' in message_content_lower:
      await message.reply("Zeka Kübü <@474944711358939170>")  # kaya tag

    if message_content_lower == "ping":
      await message.reply(f"PONG, ping: {round(self.latency * 1000)}ms")

    if message_content_lower == "katıl":
      if not isinstance(user, discord.Member) or guild is "DM":
        await message.reply("bu komut sadece sunucukarda kullanılabilir.")
        return
      if user.voice is None:
        await message.reply("herhangi bir ses kanalında değilsin!")
        return
      kanal = user.voice.channel
      if kanal is not None:
        print(kanal.mention + "a katılınıyor")
        await kanal.connect()
      else:
        print("Kanal bulunamadı")

    if message_content_lower == "çık:":
      if self.voice_clients and self.voice_clients[0]:
        kanal = self.voice_clients[0].channel
        if isinstance(kanal, discord.VoiceProtocol):
          await kanal.disconnect(force=False)

    if message_content_lower == "rastgele katıl":
      if not isinstance(guild, discord.Guild):
        await message.reply("Bir hata oluştu, lütfen tekrar deneyin")
        return
      if len(guild.voice_channels) == 0:
        await message.reply("Sunucuda ses kanalı bulunamadı")
        return

      kanallar = guild.voice_channels
      kanal = kanallar[random.randint(1, 11)]
      await kanal.connect()

    if message_content_lower == "söyle":
      if len(message.content.split(" ")) > 1:
        await message.channel.send(" ".join(message.content.split(" ")[1:]))
      else:
        await message.reply("Ne söyleyeyim?")

    if message.content.startswith("oluştur"):
      split = message_content.split(" ")
      if not len(split) > 2:
        await message.reply("Ne oluşturayım?")
        return
      if custom_responses[split[1]] is not None:
        await message.reply(f"Bu komut zaten var: {custom_responses[split[1]]}")
        return
      custom_responses[split[1]] = split[2:]
      embed = discord.Embed(title="Yeni özel komut oluşturuldu:", color=CYAN)
      embed.add_field(name="Söylenen: ", value=split[1], inline=True)
      embed.add_field(name="Botun cevabı: ",
                      value=message_content.split(" ")[2],
                      inline=True)
      await message.reply(embed=embed)

    if message.content.startswith("sustur"):
      if guild == "DM":
        await message.reply("Bu komut sadece sunucularda çalışır!")
        return
      if str(message.author) == "braven#8675":
        await message.reply("Salak Braven")
      else:
        message_content = message.content
        name = message_content.split(" ")[1]
        member = discord.utils.get(guild.members, name=name)
        if member is not None:
          await message.reply(name + " Susturluyor")
          await member.edit(mute=True)
        else:
          await message.reply("Kişi Anlaşılamadı lütfen tekrar deneyin")

    elif message.content.startswith("aç"):
      if message.guild is None:
        await message.reply("Bu komut sadece sunucularda kullanılabilir.")
        return
      message_content = message.content
      name = message_content.split(" ")[1]
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
        await message.reply(f"{name} adlı kişi bulunamadı, lütfen tekrar deneyin!")

    elif message.content.startswith("sağırlaştır"):
      if message.guild is None:
        await message.reply("BU konmut sadece sunucularda kullanılabilir.")
        return
      message_content = message.content
      name = message_content.split(" ")[1]
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
        await message.reply(message_content.split(" ")[1])


client = MyClient()


def get_client_instance():
  return client


def get_custom_responses():
  return custom_responses


def get_birthdays():
  return birthdays
