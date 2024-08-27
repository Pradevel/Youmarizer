import os
import threading
import wave
import yt_dlp
import json
from vosk import Model, KaldiRecognizer
from pydub import AudioSegment
from queue import Queue
from transformers import pipeline
from rake_nltk import Rake

model_path = "./vosk-model-small-en-us-0.15"
model = Model(model_path)

def extract_keyphrases(text):
    r = Rake()
    r.extract_keywords_from_text(text)
    keyphrases = r.get_ranked_phrases()
    return keyphrases

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

def recognize_speech_from_chunk(chunk_files, chunk_indices, result_queue):
    for chunk_file, index in zip(chunk_files, chunk_indices):
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

        result_queue.put((index, recognized_text))

def process_audio(input_file, model_path, chunk_length_ms=60000, num_threads=5):
    model = Model(model_path)
    output_dir = "chunks"
    chunks = split_audio(input_file, chunk_length_ms, output_dir)

    chunk_groups = [chunks[i::num_threads] for i in range(num_threads)]
    chunk_indices_groups = [list(range(i, len(chunks), num_threads)) for i in range(num_threads)]

    result_queue = Queue()
    threads = []

    for chunk_group, chunk_indices_group in zip(chunk_groups, chunk_indices_groups):
        thread = threading.Thread(target=recognize_speech_from_chunk, args=(chunk_group, chunk_indices_group, result_queue))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    sorted_results = [None] * len(chunks)
    while not result_queue.empty():
        index, text = result_queue.get()
        sorted_results[index] = text

    full_text = " ".join(filter(None, sorted_results))
    return full_text

def convert_to_mono(input_audio, output_audio):
    sound = AudioSegment.from_file(input_audio)
    mono_sound = sound.set_channels(1)
    mono_sound.export(output_audio, format="wav")

def download_video_as_wav(url, output_file="audio"):
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


def summarize_text(text, max_chunk_length=1024):
    summarizer = pipeline("summarization")

    def split_text(text, max_length):
        return [text[i:i + max_length] for i in range(0, len(text), max_length)]

    chunks = split_text(text, max_chunk_length)
    summaries = []
    for chunk in chunks:
        summary = summarizer(chunk, max_length=50, min_length=30, do_sample=False)
        summaries.append(summary[0]['summary_text'])

    full_summary = " ".join(summaries)
    return full_summary

video_url = 'https://www.youtube.com/watch?v=u4hBRjym-A4'
output_file = 'audio.wav'

download_video_as_wav(video_url)
print("Now recognizing")

text = process_audio(output_file, model_path, chunk_length_ms=60000, num_threads=5)
print("Transcription:", text)

print("Now summarizing")
summary = summarize_text(text)
print("Summary:", summary)
keyphrases = extract_keyphrases(text)
print("Key Phrases:", keyphrases)