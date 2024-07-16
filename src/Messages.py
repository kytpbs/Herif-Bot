import logging

from discord import Client, Message, Member

from src.message_handeler import message_command


def is_in(*search_strings: str):
    def check(message: Message):
        message_content = message.content.lower()
        for search_string in search_strings:
            if search_string in message_content:
                return True
        return False

    return check


@message_command("ping")
async def ping(client: Client, message: Message):
    await message.reply(f"PONG, ping: {round(client.latency * 1000)}ms")


@message_command("katıl")
async def join(client: Client, message: Message):
    if not isinstance(message.author, Member) or message.guild is None:
        await message.reply("bu komut sadece sunucularda kullanılabilir.")
        return
    if message.author.voice is None:
        await message.reply("herhangi bir ses kanalında değilsin!")
        return
    kanal = message.author.voice.channel
    if kanal is not None:
        logging.debug(f"Joining {kanal.name}")
        await kanal.connect()
    else:
        logging.debug("User is not in a voice channel.")
        await message.reply("herhangi bir ses kanalında değilsin!")


@message_command("söyle")
async def echo(client: Client, message: Message):
    if len(message.content.split(" ")) > 1:
        await message.channel.send(" ".join(message.content.split(" ")[1:]))
    else:
        await message.reply("Ne söyleyeyim?")


@message_command(is_in("kaya"))
async def kaya(client: Client, message: Message):
    await message.reply("Zeka Kübü <@474944711358939170>")  # kaya tag


@message_command(is_in("tuna"))
async def tuna(client: Client, message: Message):
    await message.channel.send("<@725318387198197861>")  # tuna tag


@message_command(is_in("nerde", "nerede", "neredesin", "nerdesin"))
async def where(client: Client, message: Message):
    son_mesaj = message.content.lower().split(" ")[-1]
    await message.reply(
        f'Ebenin amında. Ben sonu "{son_mesaj}" diye biten bütün mesajlara cevap vermek için kodlanmış bi botum. Seni kırdıysam özür dilerim.'
    )
