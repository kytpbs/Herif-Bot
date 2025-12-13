import logging
from datetime import datetime

import discord

from Constants import CYAN, DELETED_MESSAGES_CHANNEL_ID, GENERAL_CHAT_ID, BOSS_BOT_CHANNEL_ID
from src.data.data_manager import DataManager
from src.llm_system.llm_errors import LLMError, NoTokenError, RanOutOfMoneyError
from src.llm_system import gpt
from src import file_handeler
from src.message_handeler import call_command
import src.Messages # pylint: disable=unused-import # to register the message commands
from src.Helpers import helper_functions
from src import member_update_handlers as member_handlers
from src.Helpers.helper_functions import DiskDict, get_general_channel
from src.Tasks import start_tasks

custom_responses = DiskDict('responses.json')
birthdays = DiskDict("birthdays.json")


# noinspection PyMethodMayBeStatic
class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.deleted = False
        self.synced = False
        self.old_channel = None
        self._data_manager = DataManager()

    @property
    def data_manager(self) -> DataManager:
        return self._data_manager

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            from src import command_controller # pylint: disable=import-outside-toplevel # to avoid circular imports
            tree = command_controller.create_tree(self)
            command_controller.setup_commands(tree)
            await tree.sync()
            start_tasks()
            self.synced = True
        logging.info("Logged on as %s", self.user)

    async def on_member_join(self, member: discord.Member):
        logging.debug("%s, joined %s",member.name, member.guild.name)
        general_channel = get_general_channel(member.guild)
        if general_channel is not None:
            await general_channel.send(
                f"Zeki bir insan varlığı olan {member.mention} Bu saçmalık {member.guild} serverına katıldı. Hoş geldin!")

    async def on_member_remove(self, member: discord.Member):
        logging.debug("%s, left %s", member.name, member.guild.name)
        channel = get_general_channel(member.guild)
        if isinstance(channel, discord.TextChannel):
            await channel.send("Zeki bir insan valrlığı olan " + "**" + str(member) +
                               "**" + " Bu saçmalık serverdan ayrıldı")

    async def on_guild_channel_create(self, channel):
        logging.debug("At %s, %s was created.",channel.guild.name, channel)

        deleted_messages_channel = self.get_channel(DELETED_MESSAGES_CHANNEL_ID)
        if isinstance(deleted_messages_channel, discord.TextChannel):
            await deleted_messages_channel.send(
                f"**{channel}** adlı kanal oluşturuldu")

    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        logging.debug("At %s, %s was deleted.", channel.guild.name, channel)
        deleted_messages_channel = self.get_channel(DELETED_MESSAGES_CHANNEL_ID)
        if isinstance(deleted_messages_channel, discord.TextChannel):
            message = await deleted_messages_channel.send(
                f"**{channel}** adlı kanal silindi geri oluşturmak için reaksiyon verin (içindeki yazı kurtarılamıyor, sadece son silinen kanal kurtarılabilir)")
            await message.add_reaction("🔙")
            self.old_channel = channel
            self.deleted = True

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        embed = discord.Embed(title=f"{after.mention} adlı kişi profilini değiştirdi", color=CYAN)
        avatar = after.avatar if after.avatar is not None else after.default_avatar
        embed.set_thumbnail(url=avatar.url)

        await member_handlers.handle_profile_change(before,after, embed)

        channel = self.get_channel(BOSS_BOT_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            raise ValueError(f"Channel Not Found! Searched id: {BOSS_BOT_CHANNEL_ID}")
        if len(embed.fields) == 0:
            logging.warning(f"{before.name}'s profile was updated, but nothing changed, we probably missed something.")
            return
        await channel.send(embed=embed)

    async def on_member_ban(self, guild: discord.Guild, user: discord.Member):
        channel = get_general_channel(guild)
        logging.debug(f"{user.name} was banned from {guild.name}")
        if isinstance(channel, discord.TextChannel):
            await channel.send("Ah Lan " + str(user) + " Adlı kişi " + str(guild) +
                               " serverından banlandı ")
            return
        raise ValueError(f"Kanal Bulunamadı: aranan id: {GENERAL_CHAT_ID}")

    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        logging.debug(f"{user.name} was unbanned from {guild.name}")
        embed = discord.Embed(title=f"{user.name} bu mal gibi sunucuya geri girme hakkı kazandı", color=CYAN)
        channel = self.get_channel(GENERAL_CHAT_ID)
        if isinstance(channel, discord.TextChannel):
            await channel.send(
                f"{user.name} bu mal gibi {guild.name} sunucusuna geri girebilme hakkı kazanmılştır"
            )
        text_channel = guild.text_channels[0]
        invite = await text_channel.create_invite(reason="Ban kaldırıldı, sunucuya geri davet ediliyor", max_uses=1)
        try:
            await user.send(f"Artık {guild.name} sunucusuna geri girebilirsin! işte giriş linkin: {invite}")
            embed.description = "Davet linki kişiye gönderildi"
        except discord.Forbidden:
            logging.info(f"Couldn't send message to {user.name}")
            embed.description = "Davet linki kişiye gönderilemedi, lütfen gönderin"
        channel = self.get_channel(GENERAL_CHAT_ID)
        if isinstance(channel, discord.TextChannel):
            await channel.send(embed=embed)

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

        send_channel = self.get_channel(DELETED_MESSAGES_CHANNEL_ID)

        if not isinstance(send_channel, discord.TextChannel):
            logging.error("Text Channel Not Found! Searched id: %d",DELETED_MESSAGES_CHANNEL_ID)
            return

        who_deleted = await helper_functions.get_deleting_person(message)
        embed = discord.Embed(
            title="Mesaj silindi.", description=f"Silinen Mesaj: {message.content} ",
            color=CYAN)

        embed.add_field(name="Silinen kanal:", value=message.channel, inline=False)
        embed.add_field(name="Gönderen kişi:", value=message.author, inline=False)

        if who_deleted is not None:
            embed.add_field(name="Silen kişi:", value=who_deleted, inline=False)

        files: list[discord.File] = []
        if message.attachments is not None:
            for attachment in message.attachments:
                file = file_handeler.get_deleted_attachment(attachment)

                if file is None:
                    logging.info("Attachment not found: %s", attachment.filename)
                    continue
                files.append(file)

                if len(message.attachments) == 1:
                    embed.set_image(url="attachment://" + str(attachment.id) + "." + attachment.filename.split(".")[-1])
                else:
                    pass # don't set the image, because it's will still be displayed correctly

        await send_channel.send(embeds=[embed] + message.embeds, files=files)
        # do not delete the attachment, because it breaks the upload

    async def on_message(self, message: discord.Message):
        user = message.author
        channel = message.channel
        guild = message.guild

        time = datetime.now().strftime("%H:%M:")
        if guild is None:
            guild = "DM"
        data = f'{str(guild)} {str(channel)} / {str(user.name)}: {str(message.content)}'
        logging.getLogger("chat").debug(data)

        if message.author == self.user:
            return

        # download all attachments for on_delete
        await file_handeler.download_all_attachments(message)

        if isinstance(channel, discord.DMChannel) or message.guild is None:
            async with channel.typing():
                await self.on_dm(message)
            return

        if custom_responses.get(message.content) is not None:
            await message.reply(custom_responses[message.content])

        if time == "06:11:":  # 9:11 for +3 timezone
            await channel.send("🛫🛬💥🏢🏢")

        # call all messages that have been created in other files.
        await call_command(message, self)

    @staticmethod
    async def on_dm(message: discord.Message):
        if not isinstance(message.channel, discord.DMChannel):
            raise ValueError("This function is only for DMs")
        if message.content == "":
            return
        try:
            answer = await gpt.message_chat(message)
        except NoTokenError as e:
            await message.reply("Zeki sistemi devre dışı bırakıldı, çalışması için yöneticiyle iletişime geçin")
            raise e # re-raise the error to log it
        except RanOutOfMoneyError as e:
            await message.reply("Fakirlik vurdu, düzeltilmesini bekleyin, bu biraz zaman alabilir")
            raise e # re-raise the error to log it
        except LLMError as e:
            await message.reply("Bir şeyler ters gitti... lütfen sonra tekrar dene")
            raise e # re-raise the error to log it
        await message.reply(str(answer)) # not using an embed because it's easier to parse history this way.

client = MyClient()


def get_client_instance():
    return client


def get_custom_responses():
    return custom_responses


def get_birthdays():
    return birthdays
