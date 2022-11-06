import discord

client = discord.Client()


@client.event
async def on_message(message):
    a = True
    x = message.content
    print("Mesajın Geldiği Kanal: " + str(message.channel))
    print("Gönderen " + str(message.author))
    print("Gelen Mesaj: " + x)

    while a:
        do = input("Ne yapmak istersin?(R/S): ")

        if do == "S":
            send = input("Ne göndermek istersin?: ")
            print("Gönderildi: " + send)
            await message.channel.send(send)
            a = False
        elif do == "s":
            send = input("Ne göndermek istersin?: ")
            print("Gönderildi: " + send)
            await message.channel.send(send)
            a = False
        elif do == "R":
            send = input("Ne göndermek istersin?: ")
            print("Cevaplandı " + send)
            await message.reply(send)
            a = False
        elif do == "r":
            send = input("Ne göndermek istersin?: ")
            print("Cevaplandı " + send)
            await message.reply(send)
            a = False

        else:
            print("Anlaşılmadı... tekrar dene")
            a = True


#    print(str(ctx.message.author))
#    print(str(ctx.message.channel)
#    print(str(ctx.message.content


client.run("ODQ3MDg0NDI0MDk2NTE0MTAw.GT7saJ.RxPgMDvlAUvLE0CqODqddGjoomJ46sGlLrLT-Y")
