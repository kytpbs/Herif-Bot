#TODO: Find a better name for this file
import discord
from discord import app_commands

from Constants import BOT_NAME
from src.commands.command_group import CommandGroup


class MessagesCommands(CommandGroup):
    @classmethod
    def get_commands(cls) -> list[discord.app_commands.Command | discord.app_commands.Group | discord.app_commands.ContextMenu]:
        return [
            fake_message,
            pin_message,
        ]


@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.command(name="sahte_mesaj")
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
@app_commands.context_menu(name="Mesajı_Sabitle")
async def pin_message(interaction: discord.Interaction, message: discord.Message):
    await message.pin(reason=f"{interaction.user.name} Adlı kişi tarafından sabitlendi")
    await interaction.response.send_message(
        f"{message.author.mention} adlı kişinin; **{message.content}** mesajı sabitlendi", ephemeral=True)


