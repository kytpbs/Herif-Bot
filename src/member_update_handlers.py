import logging
import discord


async def handle_profile_change(before: discord.Member, after: discord.Member, embed: discord.Embed):
    if before.nick != after.nick:
        await handle_nick_change(before, after, embed)

    if before.avatar != after.avatar:
        await handle_avatar_change(before, after, embed)

    if before.roles != after.roles:
        await handle_roles_change(before, after, embed)

    if before.status != after.status:
        await handle_status_change(before, after, embed)

    if before.activity != after.activity:
        await handle_activity_change(before, after, embed)

    if before.display_name != after.display_name:
        await handle_display_name_change(before, after, embed)

    if before.discriminator != after.discriminator:
        await handle_discriminator_change(before, after, embed)

    if before.premium_since != after.premium_since:
        await handle_boost_status_change(before, after, embed)

    if before.accent_color != after.accent_color:
        await handle_accent_color_change(before, after, embed)


async def handle_nick_change(before: discord.Member, after: discord.Member, embed: discord.Embed):
    logging.debug("%s's nickname changed from %s to %s", before.name, before.nick, after.nick)
    embed.add_field(name="Eski Nick:", value=before.nick, inline=False)
    embed.add_field(name="Yeni Nick:", value=after.nick, inline=False)


async def handle_avatar_change(before: discord.Member, after: discord.Member, embed: discord.Embed):
    logging.debug("%s's profile picture changed.", before.name)

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


async def handle_roles_change(before: discord.Member, after: discord.Member, embed: discord.Embed):
    logging.debug("%s's roles changed.", before.name)

    for role in before.roles:
        if role not in after.roles:
            embed.add_field(name="Rol Silindi:", value=role.mention, inline=False)

    for role in after.roles:
        if role not in before.roles:
            embed.add_field(name="Rol Eklendi:", value=role.mention, inline=False)


async def handle_status_change(before: discord.Member, after: discord.Member, embed: discord.Embed):
    logging.debug("%s's status changed from %s to %s", before.name, before.status, after.status)
    embed.add_field(name="Eski Durum:", value=before.status, inline=False)
    embed.add_field(name="Yeni Durum:", value=after.status, inline=False)


async def handle_activity_change(before: discord.Member, after: discord.Member, embed: discord.Embed):
    logging.debug(f"{before.name}'s activity changed from {before.activity} to {after.activity}")
    embed.add_field(name="Eski Aktivite:", value=before.activity, inline=False)
    embed.add_field(name="Yeni Aktivite:", value=after.activity, inline=False)


async def handle_display_name_change(before: discord.Member, after: discord.Member, embed: discord.Embed):
    before_name = before.display_name if before.display_name is None else before.name
    after_name = after.display_name if after.display_name is None else after.name
    logging.debug(f"{before.name}'s name changed from {before.name} to {after.name}")
    embed.add_field(name="Eski İsim:", value=before_name, inline=False)
    embed.add_field(name="Yeni İsim:", value=after_name, inline=False)


async def handle_discriminator_change(before: discord.Member, after: discord.Member, embed: discord.Embed):
    logging.debug(f"{before.name}'s discriminator changed from {before.discriminator} to {after.discriminator}")
    embed.add_field(name="Eski Discriminator:", value=before.discriminator, inline=False)
    embed.add_field(name="Yeni Discriminator:", value=after.discriminator, inline=False)


async def handle_boost_status_change(before: discord.Member, after: discord.Member, embed: discord.Embed):
    logging.debug(f"{before.name}'s boost status changed from {before.premium_since} to {after.premium_since}")
    embed.add_field(name="Eski Boost Durumu:", value=before.premium_since, inline=False)
    embed.add_field(name="Yeni Boost Durumu:", value=after.premium_since, inline=False)


async def handle_accent_color_change(before: discord.Member, after: discord.Member, embed: discord.Embed):
    logging.debug(f"{before.name}'s accent color changed from {before.accent_color} to {after.accent_color}")
    embed.add_field(name="Eski Renk:", value=before.accent_color, inline=False)
    embed.add_field(name="Yeni Renk:", value=after.accent_color, inline=False)


async def handle_desktop_status_change(before: discord.Member, after: discord.Member, embed: discord.Embed):
    logging.debug(f"{before.name}'s desktop status changed from {before.desktop_status} to {after.desktop_status}")
    embed.add_field(name="Eski Masaüstü Durumu:", value=before.desktop_status, inline=False)
    embed.add_field(name="Yeni Masaüstü Durumu:", value=after.desktop_status, inline=False)


async def handle_mobile_status_change(before: discord.Member, after: discord.Member, embed: discord.Embed):
    logging.debug(f"{before.name}'s mobile status changed from {before.mobile_status} to {after.mobile_status}")
    embed.add_field(name="Eski Mobil Durumu:", value=before.mobile_status, inline=False)
    embed.add_field(name="Yeni Mobil Durumu:", value=after.mobile_status, inline=False)


async def handle_web_status_change(before: discord.Member, after: discord.Member, embed: discord.Embed):
    logging.debug(f"{before.name}'s web status changed from {before.web_status} to {after.web_status}")
    embed.add_field(name="Eski Web Durumu:", value=before.web_status, inline=False)
    embed.add_field(name="Yeni Web Durumu:", value=after.web_status, inline=False)


async def handle_is_on_mobile_change(before: discord.Member, after: discord.Member, embed: discord.Embed):
    logging.debug(f"{before.name}'s mobile status changed from {before.is_on_mobile()} to {after.is_on_mobile()}")
    embed.add_field(name="Eski Mobil Durumu:", value=before.is_on_mobile(), inline=False)
    embed.add_field(name="Yeni Mobil Durumu:", value=after.is_on_mobile(), inline=False)
