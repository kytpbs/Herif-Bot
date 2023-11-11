import discord


def get_general_channel(guild: discord.Guild):
    for channel in guild.text_channels:
        if "genel" in channel.name.lower() or "general" in channel.name.lower():
            return channel
    return None

