import yt_dlp as youtube_dl
import speech_recognition as sr
from transformers import pipeline
import os
import subprocess


def download_audio(url, base_filename="audio"):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': base_filename,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'verbose': True,
    }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        mp3_file = f"{base_filename}.mp3"
        if not os.path.exists(mp3_file):
            raise FileNotFoundError(f"Expected file {mp3_file} was not created.")

        return mp3_file
    except Exception as e:
        print(f"Error downloading audio: {e}")
        return None


def convert_mp3_to_wav(mp3_file, wav_file="audio.wav"):
    if not os.path.exists(mp3_file):
        print(f"MP3 file {mp3_file} does not exist. Conversion cannot proceed.")
        return

    try:
        subprocess.run([
            'ffmpeg', '-i', mp3_file,
            '-ar', '16000', '-ac', '1',
            wav_file
        ], check=True)
        print(f"Converted {mp3_file} to {wav_file}")

        # Check if the WAV file was generated and log its size
        if os.path.exists(wav_file):
            wav_size = os.path.getsize(wav_file)
            print(f"WAV file generated: {wav_file}, Size: {wav_size} bytes")
        else:
            print(f"WAV file {wav_file} was not generated.")

    except subprocess.CalledProcessError as e:
        print(f"Error converting MP3 to WAV: {e}")


def transcribe_audio(audio_file):
    if not os.path.exists(audio_file):
        print(f"Audio file {audio_file} does not exist.")
        return ""

    recognizer = sr.Recognizer()
    try:
        print(f"Starting transcription of {audio_file}")
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
            print("Transcription successful!")
            return text
    except sr.RequestError:
        print("API unavailable or unresponsive")
    except sr.UnknownValueError:
        print("Unable to recognize speech")
    except Exception as e:
        print(f"Error during transcription: {e}")
    return ""


def summarize_text(text):
    summarizer = pipeline("summarization", model="facebook/bart-small")
    summary = summarizer(text, max_length=150, min_length=50, do_sample=False)
    return summary[0]['summary_text']


def process_audio(youtube_url):
    mp3_file = download_audio(youtube_url)
    if mp3_file:
        convert_mp3_to_wav(mp3_file)

        # Add a check to see if the WAV file exists before transcribing
        wav_file = "audio.wav"
        if os.path.exists(wav_file):
            transcription = transcribe_audio(wav_file)
            if transcription:
                summary = summarize_text(transcription)
                print("Summary:\n", summary)
        else:
            print(f"WAV file {wav_file} not found, skipping transcription.")


# Main execution
youtube_url = "https://www.youtube.com/watch?v=oFeSRI8TcwI"
process_audio(youtube_url)

# Clean up files
if os.path.exists("audio.mp3"):
    os.remove("audio.mp3")
if os.path.exists("audio.wav"):
    os.remove("audio.wav")