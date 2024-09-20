import logging
from datetime import datetime
import functools
from typing import Optional

import discord
from discord import app_commands

from src.sql.responses import AlreadyExistsError, TooManyAnswersError
from src.llm_system import gpt
from src.llm_system.llm_errors import LLMError
import src.client as client
from Constants import BOT_ADMIN_SERVER_ID, BOT_NAME, BOT_OWNER_ID, CYAN, KYTPBS_TAG
from src.download_system.download_commands import download_video_command
from src.Helpers.birthday_helpers import get_user_and_date_from_string
from src.voice import voice_commands
from src.voice.old_message_holder import add_message_to_be_deleted
from src.response_system import add_answer, get_answers, get_data, remove_answer

birthdays = client.get_birthdays()

admin = discord.Permissions()
admin.update(administrator=True)
discord_client = client.get_client_instance()


class VoiceCommands(app_commands.Group):
    @app_commands.command(name="çal", description="Youtube'dan bir şey çalmanı sağlar")
    async def cal(self, interaction: discord.Interaction, arat: str):
        await interaction.response.defer()
        response = await voice_commands.play(interaction, arat)
        message = await interaction.followup.send(
            """
            _Bu özellik `/çal` ile aynı şeyi yapıyor, lütfen bundan sonra `/ses çal` yerine '/çal' kullanın._
            _Eğer düğmeler bozulur ise: `/çalan` komutunu kullanabilirsin_\n\n
            """ + response.message,
            embed=response.embed,
            ephemeral=response.ephemeral,
            view=response.view,
            wait=True,
        )
        add_message_to_be_deleted(interaction.guild_id, message)



@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
class AiCommands(app_commands.Group):
    @app_commands.command(name="soru", description="bota bir soru sor")
    async def chatgpt(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer(ephemeral=False)
        try:
            answer = await gpt.interaction_chat(interaction, message, include_history=False)
        except LLMError:
            await interaction.followup.send("Bir şey ters gitti, lütfen tekrar deneyin", ephemeral=True)
            raise
        await interaction.followup.send(answer)

    @app_commands.command(name="sohbet", description="Botun sohbete katılmasını sağlar! (eski mesaj okur!)")
    async def question(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer(ephemeral=False)
        try:
            answer = await gpt.interaction_chat(interaction, message)
        except LLMError:
            await interaction.followup.send("Bir hata oluştu, lütfen tekrar deneyin", ephemeral=True)
            raise # re-raise the error so that the error is logged
        await interaction.followup.send(answer)

class BirthdayCommands(app_commands.Group):
    @app_commands.command(name="dogumgunu_ekle", description="Doğumgününü eklemeni sağlar")
    async def add_birthday(self, interaction: discord.Interaction, day: str, month: str, year: str,
                           user: discord.Member = None):  # type: ignore
        if user is None:
            user = interaction.user  # type: ignore
        user_id = user.id
        date = datetime(int(year), int(month), int(day))
        date_string = str(date.year) + "-" + str(date.month) + "-" + str(date.day)
        if user_id in birthdays and birthdays[str(user_id)] is not None:
            await interaction.response.send_message(
                f"{user.mention} adlı kişinin doğum günü zaten '{birthdays[str(user_id)]}' olarak ayarlanmış " +
                f"Değiştirmek için lütfen {KYTPBS_TAG} kişisine ulaşın", ephemeral=True)
            return
        birthdays[str(user_id)] = date_string
        await interaction.response.send_message(
            f"{user.mention} adlı kişinin doğum günü '{date_string}' olarak ayarlandı")

    @app_commands.command(name="dogumgunu_goster", description="Kişinin doğumgününü gösterir")
    async def show_birthday(self, interaction: discord.Interaction, user: discord.Member):
        user_id = str(user.id)
        if birthdays.get(user_id) is not None:
            await interaction.response.send_message(f"{user.mention} adlı kişinin doğum günü '{birthdays[user_id]}'")
            return
        await interaction.response.send_message(f"{user.mention} adlı kişinin doğum günü kayıtlı değil",
                                                ephemeral=True)


class AdminBirthdayCommands(app_commands.Group):
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
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Sadece Sunucularda çalışır")
            return
        if (interaction.user != user and not interaction.user.guild_permissions.administrator) or user.guild.id != BOT_ADMIN_SERVER_ID:
            await interaction.response.send_message("Sadece Kendi Doğumgününü Silebilirsin", ephemeral=True)
            return
        user_id = str(user.id)
        if birthdays.get(user_id) is None:
            await interaction.response.send_message(f"{user.mention} adlı kişinin doğum günü zaten kayıtlı değil",
                                                    ephemeral=True)
            return
        del birthdays[user_id]
        await interaction.response.send_message(f"{user.mention} adlı kişinin doğum günü silindi")


class SpecialCommands(app_commands.Group):
    @app_commands.command(name="olustur", description="botun senin ayarladığın mesajlara cevap verebilmesini sağlar")
    async def create_command(self, interaction: discord.Interaction, text: str, answer: str):
        if interaction.guild_id is None:
            await interaction.response.send_message("Bu komut sadece sunucularda çalışır", ephemeral=True)
            return
        try:
            result = add_answer(text, answer, guild_id=str(interaction.guild_id))
            if not result:
                await interaction.response.send_message("Bilinmeyen bir hata oluştu, lütfen daha sonra tekrar deneyin", ephemeral=True)
            else:
                embed = discord.Embed(title="Yeni Cevap Oluşturuldu", description=f"artık '{text}' yazıca '{answer}' diyecek", color=CYAN)
                await interaction.response.send_message(embed=embed)
            return
        except AlreadyExistsError:
            logging.error("Failed to add response: %s in guild: %s", text, interaction.guild_id)
            await interaction.response.send_message(f"'{text}' deyince zaten '{answer}' diyor", ephemeral=True)
            return
        except TooManyAnswersError as e:
            answers = e.current_answers

        is_admin = isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator

        description = "Bu mesaj için çok fazla cevap var"
        description += ", değiştirmek için `admin_sil` komutunu kullanın" if is_admin else "."
        embed = discord.Embed(title="Çok Fazla Cevap", description=description, color=CYAN)

        for i, actual_answer in enumerate(answers):
            embed.add_field(name=f"Cevap {i + 1}", value=actual_answer, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="cevaplar", description="Bütün özel eklenmiş cevapları gösterir")
    async def answers(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Özel Cevaplar", color=CYAN)
        embed.description = "Özel eklenmiş cevaplar"
        guild_id = str(interaction.guild_id) if interaction.guild_id else None
        for i, (question, answer) in enumerate(get_data(guild_id)):
            if i >= 24:
                embed.description += "\n\nDaha fazla cevap var, 25 ten fazlası gösterilmiyor"
                break
            embed.add_field(name=question, value=answer, inline=False)
        await interaction.response.send_message(embed=embed)


class AdminSpecialCommands(app_commands.Group):
    @app_commands.command(name="sil", description="Sunucuda özel eklenmiş bir cevabı siler")
    async def delete_command(self, interaction: discord.Interaction, question: str, answer: str):
        if interaction.guild_id is None:
            await interaction.response.send_message("Bu komut sadece sunucularda çalışır", ephemeral=True)
            return
        is_deleted = remove_answer(question, answer, str(interaction.guild_id))
        if is_deleted:
            embed = discord.Embed(title="Cevap Silindi", description=f"'{question}: {answer}' adlı cevap silindi", color=CYAN)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"{question} a {answer} cevap verme zaten yok...", ephemeral=True)

    @app_commands.command(name="interaktif-sil", description="Sunucuda özel eklenmiş bir cevabı siler, seçim yapmanı sağlar")
    async def interactive_delete(self, interaction: discord.Interaction, question: str):
        if interaction.guild_id is None:
            await interaction.response.send_message("Bu komut sadece sunucularda çalışır", ephemeral=True)
            return

        guild_id = str(interaction.guild_id)
        answers = get_answers(question, guild_id)
        view = discord.ui.View()
        for answer in answers:
            button = discord.ui.Button(style=discord.ButtonStyle.danger, label=answer, custom_id=answer)
            button.callback = functools.partial(self.delete_command.callback, question=question, answer=answer) #pylint: disable=no-member
            view.add_item(button)
        await interaction.response.send_message("Hangi cevabı silmek istersin?", view=view)

class AdminServerCommands(app_commands.Group):
    @app_commands.command(name="run-code", description="Runs any code you want")
    async def run_code(self, interaction: discord.Interaction, code: str):
        if interaction.user.id == BOT_OWNER_ID:
            pass # if the user is the bot owner, then they can use this command
        elif interaction.guild_id is None or interaction.guild_id != BOT_ADMIN_SERVER_ID:
            await interaction.response.send_message("This command can only be used in the bot admin server", ephemeral=True)
            return
        elif not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command", ephemeral=True)
            return

        from contextlib import (
            redirect_stdout,  # pylint: disable=import-outside-toplevel #this is a command for admins only
        )
        from io import (
            StringIO,  # pylint: disable=import-outside-toplevel #this is a command for admins only
        )

        with StringIO() as buf, redirect_stdout(buf):
            data = None
            try:
                data = eval(code, globals()) #pylint: disable=eval-used #this is a command for admins only
            except Exception as e:  #pylint: disable=broad-exception-caught  #this is a command for admins only, and we want to catch all errors so we can send them to the user
                data = e
            finally:
                data_str = "" if data is None else str(data)
                embed = discord.Embed(title="Code Output", description=f"{buf.getvalue()}{data_str}", color=CYAN)
                await interaction.response.send_message(embed=embed, ephemeral=isinstance(data_str, Exception))

tree = app_commands.CommandTree(discord_client)

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@tree.command(name="feridun_abi", description="Yine seks hikayesi mi yazıyorsun feridun abi?")
async def story_writer(interaction: discord.Interaction, message: str):
    await interaction.response.defer(ephemeral=False)
    try:
        answer = await gpt.story_writer(interaction, message)
    except LLMError:
        await interaction.followup.send("Bir şey ters gitti, lütfen tekrar deneyin", ephemeral=True)
        raise
    if len(answer) < 2000:
        await interaction.followup.send(answer)
        return
    for i in range(0, len(answer), 2000):
        await interaction.followup.send(answer[i:i + 2000])

@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@tree.command(name="sahte_mesaj")
async def fake_message(interaction: discord.Interaction, user: discord.Member, message: str):
    channel = interaction.channel
    if not isinstance(channel, discord.TextChannel):
        await interaction.response.send_message("Cannot use in non-text channels", ephemeral=True)
        return

    webhooks = await channel.webhooks()
    for webhook in webhooks:
        if webhook.name == BOT_NAME + "_fake_message_webhook":
            message_webhook = webhook
            break
    else:
        message_webhook: discord.Webhook = await channel.create_webhook(name=BOT_NAME + "_fake_message_webhook")

    avatar_url = user.avatar.url if user.avatar else discord.utils.MISSING
    await message_webhook.send(content=message, username=user.display_name, avatar_url=avatar_url)
    await interaction.response.send_message("Gizli Mesaj Gönderildi", ephemeral=True)


@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@tree.command(name="çal")
async def new_play(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    response = await voice_commands.play(interaction, url)
    message = await interaction.followup.send(response.message + "\n\n _Eğer düğmeler bozulur ise: `/çalan` komutunu kullan_", embed=response.embed, ephemeral=response.ephemeral, view=response.view, wait=True)
    add_message_to_be_deleted(interaction.guild_id, message)


@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@tree.command(name="çalan", description="Eğer çal düğmeleri çalışmıyorsa, bu komutu kullanarak yenileyebilirsin")
async def playlist(interaction: discord.Interaction):
    response = voice_commands.get_currently_playing_music_message(interaction)
    await interaction.response.send_message(response.message, embed=response.embed, ephemeral=response.ephemeral, view=response.view)
    add_message_to_be_deleted(interaction.guild_id, await interaction.original_response())



@tree.error
async def on_error(interaction: discord.Interaction, error: Exception):
    logging.error("An error occurred while processing an interaction", exc_info=error)
    if interaction.response.is_done():
        await interaction.followup.send("Bilinmeyen bir hata, lütfen tekrar deneyin", ephemeral=True)
    else:
        await interaction.response.send_message("Bilinmeyen bir hata, lütfen tekrar deneyin", ephemeral=True)

@tree.context_menu(name="Mesajı_Sabitle")
async def pin_message(interaction: discord.Interaction, message: discord.Message):
    await message.pin(reason=f"{interaction.user.name} Adlı kişi tarafından sabitlendi")
    await interaction.response.send_message(
        f"{message.author.mention} adlı kişinin; **{message.content}** mesajı sabitlendi", ephemeral=True)


@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@tree.context_menu(name="Linkteki_Videoyu_Indir")
async def download_video_link(interaction: discord.Interaction, message: discord.Message):
    content = message.content
    await download_video_command(interaction, content)

@app_commands.allowed_installs(guilds=False, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@tree.context_menu(name="Linkteki_Videoyu_Gizlice_Indir")
async def download_video_link_hidden(interaction: discord.Interaction, message: discord.Message):
    content = message.content
    await download_video_command(interaction, content, is_ephemeral=True)


@tree.command(name="ping", description="Botun pingini gösterir")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong: {round(discord_client.latency * 1000)}ms")


@tree.command(name="video-indir", description="Paylaşılan linkteki videoyu paylaşır şuan-desteklenen: twitter, instagram, youtube")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def download_video(interaction: discord.Interaction, url: str, include_title: Optional[bool] = None):
    await download_video_command(interaction, url, include_title=include_title)


def get_tree_instance():
    return tree


def setup_commands():
    voice_cmds = VoiceCommands(name="ses", description="Ses komutları!", guild_only=True)
    ai_cmds = AiCommands(name="zeki", description="Botu zeki yapan komutlar")
    special_cmds = SpecialCommands(name="özel", description="Bota özel komutlar ekleyip görmen için komutlar")
    special_admin_cmds = AdminSpecialCommands(name="admin", description="Adminlerin kullanabileceği özel komutlar",
                                              default_permissions=admin, parent=special_cmds)
    birthday_cmds = BirthdayCommands(name="doğumgünü", description="Doğumgünü komutları")
    admin_birthday_cmds = AdminBirthdayCommands(name="admin",
                                                description="Adminlerin kullanabileceği doğumgünü komutları",
                                                default_permissions=admin, parent=birthday_cmds)
    admin_server_cmds = AdminServerCommands(name="owner", description="Bot Sahibinin Kullanacağı Komutlar",
                                             default_permissions=admin, guild_only=True)
    tree.add_command(voice_cmds)
    tree.add_command(admin_birthday_cmds)
    tree.add_command(special_admin_cmds)
    tree.add_command(ai_cmds)
    tree.add_command(admin_server_cmds)
