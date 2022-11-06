import discord
from GUI import ChatApplication
client = discord.Client()



@client.event
async def on_ready():
    print("Starting")


@client.event
async def on_message(message):
    x = message.content
    print(x)
    username = message.author
    y = f"Kanal:{message.channel} {message.author}: {x}"
    message.channel.send(answer)
    ChatApplication.__init__()
    ChatApplication.run()


client.run("ODQ3MDg0NDI0MDk2NTE0MTAw.GT7saJ.RxPgMDvlAUvLE0CqODqddGjoomJ46sGlLrLT-Y")
