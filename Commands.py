import json
from datetime import datetime

import discord
import openai
from discord import app_commands

import GPT
import voice_commands as vc_cmds
import Youtube
import client
from Constants import CYAN, KYTPBS_TAG, BOT_ADMIN_SERVER_ID
from birthday_helpers import get_user_and_date_from_string

birthdays = client.get_birthdays()
custom_responses = client.get_custom_responses()
last_played = Youtube.get_last_played_guilded()

admin = discord.Permissions()
admin.administrator = True
discord_client = client.get_client_instance()


class voice_commands(app_commands.Group):
  @app_commands.command(name="kanala_katıl",
                        description="sunucuda belirli bir kanala ya da senin olduğun bir kanala katılır")
  async def channel_join(self, interaction: discord.Interaction, channel: discord.VoiceChannel = None):  # type: ignore
    await vc_cmds.join(interaction, channel)

  @app_commands.command(name="duraklat", description="Sesi duraklatır")
  async def dur(self, interaction: discord.Interaction):
    await vc_cmds.pause(interaction)

  @app_commands.command(name="devam_et", description="Sesi devam ettirir")
  async def devam_et(self, interaction: discord.Interaction):
    await vc_cmds.resume(interaction)

  @app_commands.command(name="çık", description="Ses Kanalından çıkar")
  async def cik(self, interaction: discord.Interaction):
    await vc_cmds.leave(interaction)

  @app_commands.command(name="çal", description="Youtubedan bir şey çalmanı sağlar")
  async def cal(self, interaction: discord.Interaction, message: str):
    await vc_cmds.play(interaction, message)


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
        await interaction.response.send_message(embed=embed)
        return

    except openai.InvalidRequestError:
      embed = discord.Embed(title="HATA", description="+18 olduğu için izin verilmedi (kapatılamıyor)")
      await interaction.response.send_message(embed=embed)
      return

    except openai.OpenAIError:
      embed = discord.Embed(title="HATA", description="Bir hata oluştu, hata: 'OpenAIError'")
      await interaction.response.send_message(embed=embed)
      return

    except Exception as e:
      embed = discord.Embed(title="HATA", description=f"Bir hata oluştu: {e.__class__.__name__}")
      await interaction.response.send_message(embed=embed)
      return

    if image is None:
      embed = discord.Embed(title="HATA", description="Bir hata oluştu: 'image bulunamadı'")

    if embed.title == "HATA":
      await interaction.followup.send(embed=embed, ephemeral=True)
    await interaction.followup.send(embed=embed, ephemeral=False)


class Birthday_commands(app_commands.Group):
  @app_commands.command(name="dogumgunu_ekle", description="Doğumgününü eklemeni sağlar")
  async def add_birthday(self, interaction: discord.Interaction, day: str, month: str, year: str, user: discord.Member = None): # type: ignore 
    if user is None:
      user = interaction.user  # type: ignore
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
    if not isinstance(interaction.user, discord.Member):
      await interaction.response.send_message("Sadece Sunucularda çalışır")
      return
    if interaction.user != user and (not interaction.user.guild_permissions.administrator) or user.guild.id != BOT_ADMIN_SERVER_ID:
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


tree = app_commands.CommandTree(discord_client)

@tree.command(name="ping", description="Botun pingini gösterir")
async def ping(interaction: discord.Interaction):
  await interaction.response.send_message(f"Pong: {round(discord_client.latency * 1000)}ms")

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
