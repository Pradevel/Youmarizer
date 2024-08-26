import yt_dlp as youtube_dl

def download_audio(url, output_file="audio"):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_file,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

youtube_url = "https://www.youtube.com/watch?v=oFeSRI8TcwI"
download_audio(youtube_url)