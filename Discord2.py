import discord


def bot():
    client = discord.Client()

    @client.event
    async def on_ready():
        print("Starting")

    @client.event
    async def on_message(message):
        def answer(answer):
            await message.channel.send(answer)
        def recive():
            return f"{message.author}: {message.content} \n"
    client.run("ODQ3MDg0NDI0MDk2NTE0MTAw.GT7saJ.RxPgMDvlAUvLE0CqODqddGjoomJ46sGlLrLT-Y")

def recive():
    client = discord.Client()

    @client.event
    async def on_ready():
        print("Starting")

    @client.event
    async def on_message(message):
        x = f"{message.author}: {message.content} \n"
        return x

    client.run("ODQ3MDg0NDI0MDk2NTE0MTAw.GT7saJ.RxPgMDvlAUvLE0CqODqddGjoomJ46sGlLrLT-Y")