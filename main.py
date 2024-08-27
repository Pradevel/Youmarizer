import os
import threading
import yt_dlp
import torchaudio
from transformers import pipeline
from pydub import AudioSegment

speech_to_text = pipeline("automatic-speech-recognition", model="facebook/wav2vec2-large-960h")

def resample_audio(input_file, target_sample_rate=16000):
    audio = AudioSegment.from_wav(input_file)
    audio = audio.set_frame_rate(target_sample_rate)
    audio.export(input_file, format="wav")

def convert_to_mono(input_file):
    audio = AudioSegment.from_wav(input_file)
    mono_audio = audio.set_channels(1)
    mono_audio.export(input_file, format="wav")

def split_audio(input_file, chunk_length_ms, output_dir="chunks"):
    audio = AudioSegment.from_wav(input_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    chunks = []
    for i, chunk in enumerate(audio[::chunk_length_ms]):
        chunk_file = os.path.join(output_dir, f"chunk_{i}.wav")
        chunk.export(chunk_file, format="wav")
        convert_to_mono(chunk_file)
        resample_audio(chunk_file)
        chunks.append(chunk_file)

    return chunks

def recognize_speech_from_chunk(chunk_file, result_queue):
    waveform, sample_rate = torchaudio.load(chunk_file)
    waveform = waveform.squeeze()
    transcription = speech_to_text(waveform.numpy(), sampling_rate=sample_rate)["text"]
    result_queue.append(transcription)

def process_audio(input_file, chunk_length_ms=60000):
    chunks = split_audio(input_file, chunk_length_ms)
    print(chunks)
    result_queue = []
    threads = []

    for chunk_file in chunks:
        thread = threading.Thread(target=recognize_speech_from_chunk, args=(chunk_file, result_queue))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    full_text = " ".join(result_queue)
    return full_text

def download_video_as_wav(url, output_file="audio.wav"):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl': output_file,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

video_url = 'https://www.youtube.com/watch?v=u4hBRjym-A4'
output_file = 'audio.wav'

download_video_as_wav(video_url, 'audio')
print("Now recognizing")
text = process_audio(output_file)
print("Transcription:", text)