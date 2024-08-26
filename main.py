import os
import threading
import wave

import yt_dlp
import speech_recognition as sr
import json
from vosk import Model, KaldiRecognizer
from pydub import AudioSegment

model_path = "./vosk-model-small-en-us-0.15"
model = Model("./vosk-model-small-en-us-0.15")

def resample_audio(input_file, output_file, target_sample_rate=16000):
    audio = AudioSegment.from_wav(input_file)
    audio = audio.set_frame_rate(target_sample_rate)
    audio.export(output_file, format="wav")

def split_audio(input_file, chunk_length_ms, output_dir):
    audio = AudioSegment.from_wav(input_file)
    duration_ms = len(audio)
    chunk_count = duration_ms // chunk_length_ms + (1 if duration_ms % chunk_length_ms > 0 else 0)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    chunks = []
    for i in range(chunk_count):
        start = i * chunk_length_ms
        end = start + chunk_length_ms
        chunk = audio[start:end]
        chunk_file = os.path.join(output_dir, f"chunk_{i}.wav")
        chunk.export(chunk_file, format="wav")
        convert_to_mono(chunk_file, chunk_file)
        resample_audio(chunk_file, chunk_file)
        chunks.append(chunk_file)

    return chunks


def recognize_speech_from_chunk(chunk_file, model, result_queue):
    with wave.open(chunk_file, "rb") as wf:
        if wf.getnchannels() != 1:
            raise ValueError("Audio file must be mono")

        recognizer = KaldiRecognizer(model, wf.getframerate())
        recognized_text = ""

        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if recognizer.AcceptWaveform(data):
                result = recognizer.Result()
                recognized_text += json.loads(result)["text"] + " "

        final_result = json.loads(recognizer.FinalResult())
        recognized_text += final_result.get("text", "")

    result_queue.append(recognized_text)


def process_audio(input_file, model_path, chunk_length_ms=60000):
    model = Model(model_path)
    output_dir = "chunks"
    chunks = split_audio(input_file, chunk_length_ms, output_dir)

    result_queue = []
    threads = []
    for chunk_file in chunks:
        thread = threading.Thread(target=recognize_speech_from_chunk, args=(chunk_file, model, result_queue))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Combine results
    full_text = " ".join(result_queue)
    return full_text



def convert_to_mono(input_audio, output_audio):
    sound = AudioSegment.from_file(input_audio)
    mono_sound = sound.set_channels(1)
    mono_sound.export(output_audio, format="wav")

def recognize_speech_from_audio(wav_file):
    with wave.open(wav_file, "rb") as wf:
        if wf.getnchannels() != 1:
            return "Audio file must be mono"

        recognizer = KaldiRecognizer(model, wf.getframerate())
        recognized_text = ""
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if recognizer.AcceptWaveform(data):
                result = recognizer.Result()
                recognized_text += json.loads(result)["text"] + " "

        final_result = json.loads(recognizer.FinalResult())
        recognized_text += final_result.get("text", "")

    return recognized_text

def download_video_as_mp3(url, output_path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl': output_path + 'audio',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

video_url = 'https://www.youtube.com/watch?v=u4hBRjym-A4'
output_path = ''
download_video_as_mp3(video_url, output_path)
print("Now recognizing")
text = process_audio('audio.wav', model_path)
print(text)
