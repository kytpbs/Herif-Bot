import discord


def get_general_channel(guild: discord.Guild):
    for channel in guild.text_channels:
        name = channel.name.lower()
        if "genel" in name or "general" in name or "💬" in name:
            return channel
    return None

