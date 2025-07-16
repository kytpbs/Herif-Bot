import discord
from discord import app_commands

from Constants import CYAN
from src import client

custom_responses = client.get_custom_responses()

@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
class CustomizationCommands(app_commands.Group):
    @app_commands.command(name="olustur", description="botun senin ayarladığın mesajlara cevap verebilmesini sağlar")
    async def create_command(self, interaction: discord.Interaction, text: str, answer: str, degistir: bool = False):
        if custom_responses.get(text) is None:
            custom_responses[text] = answer
            await interaction.response.send_message(f"Yeni bir cevap oluşturuldu. {text} : {answer}")
            return

        if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(f"Bu mesaja zaten bir cevap var: {custom_responses[text]}, " +
                                                    "lütfen başka bir mesaj deneyin",
                                                    ephemeral=True)
            return

        if not degistir:
            await interaction.response.send_message(f"Bu mesaja zaten bir cevap var: {custom_responses[text]}, " +
                                                    "değiştirmek için komutta 'degistir' argümanını kullanın",
                                                    ephemeral=True)
            return


        eski_cevap = custom_responses[text]
        custom_responses[text] = answer
        embed = discord.Embed(title="Cevap Değiştirildi", description=f"'{text} : {answer}' a değiştirildi", color=CYAN)
        embed.add_field(name="Eski Cevap", value=eski_cevap, inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="cevaplar", description="Bütün özel eklenmiş cevapları gösterir")
    async def answers(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Özel Cevaplar", color=CYAN)
        embed.description = "Özel eklenmiş cevaplar"
        for i, (key, value) in enumerate(custom_responses.items()):
            if i >= 24:
                embed.description += "\n\nDaha fazla cevap var, 25 ten fazlası gösterilmiyor"
                break
            embed.add_field(name=key, value=value, inline=False)
        await interaction.response.send_message(embed=embed)


    @app_commands.command(name="sil", description="Özel eklenmiş bir cevabı siler")
    @app_commands.checks.has_permissions(administrator=True)
    async def delete_command(self, interaction: discord.Interaction, text: str):
        if custom_responses.get(text) is None:
            await interaction.response.send_message(f"Cevap bulunamadı: {text}", ephemeral=True)

        user: discord.Member = interaction.user # type: ignore
        if user.guild_permissions.administrator is False:
            await interaction.response.send_message(f"{text} mesajına zaten cevap var ve sen bu komutu kullanamazsın")
            return

        response = custom_responses[text]
        del custom_responses[text]
        embed = discord.Embed(title="Cevap Silindi", description=f"'{text}: {response}' adlı cevap silindi", color=CYAN)
        await interaction.response.send_message(embed=embed)

