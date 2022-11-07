import discord
from datetime import datetime
import time as Times
intents = discord.Intents.all()
intents.members = True



class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)
        channel = client.get_channel(847070819766108181)
        while True:
            now = (datetime.now())
            time = now.strftime("%H:%M:")
            if time == "09:11":    
                await channel.send("🛫🛬💥🏢🏢")
            Times.sleep(1)

client = MyClient(intents=intents)
client.run("ODQ3MDg0NDI0MDk2NTE0MTAw.GT7saJ.RxPgMDvlAUvLE0CqODqddGjoomJ46sGlLrLT-Y")
