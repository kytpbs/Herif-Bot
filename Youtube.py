import youtube_dl

ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': 'video.mp4',
}
mesaj= input("Enter the link: ")

with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    ydl.download([mesaj])
