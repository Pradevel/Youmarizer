import io
import json
import os
import threading
import wave
from contextlib import redirect_stdout, redirect_stderr, contextmanager
from queue import Queue

from pydub import AudioSegment
from tqdm import tqdm
from vosk import Model, KaldiRecognizer

model_path = "./vosk-model-small-en-us-0.15"

def suppress_logs(func, *args, **kwargs):
    with io.StringIO() as stdout, io.StringIO() as stderr, redirect_stdout(stdout), redirect_stderr(stderr):
        return func(*args, **kwargs)

def load_model():
    return suppress_logs(lambda: Model(model_path))

model = load_model()

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
    for i in tqdm(range(chunk_count), desc="Splitting audio", unit="chunk"):
        start = i * chunk_length_ms
        end = start + chunk_length_ms
        chunk = audio[start:end]
        chunk_file = os.path.join(output_dir, f"chunk_{i}.wav")
        chunk.export(chunk_file, format="wav")
        convert_to_mono(chunk_file, chunk_file)
        resample_audio(chunk_file, chunk_file)
        chunks.append(chunk_file)

    return chunks

def cleanup_files(audio_file, chunks_dir):
    if os.path.isfile(audio_file):
        os.remove(audio_file)
    if os.path.isdir(chunks_dir):
        for file in os.listdir(chunks_dir):
            file_path = os.path.join(chunks_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        os.rmdir(chunks_dir)


def recognize_speech_from_chunk(chunk_files, chunk_indices, result_queue):
    with tqdm(total=len(chunk_files), desc="Processing chunks") as pbar:
        for chunk_file, index in zip(chunk_files, chunk_indices):
            with wave.open(chunk_file, "rb") as wf:
                if wf.getnchannels() != 1:
                    raise ValueError("Audio file must be mono")

                with io.StringIO() as stdout, io.StringIO() as stderr, redirect_stdout(stdout), redirect_stderr(stderr):
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
            pbar.update(1)
    cleanup_files('audio.wav', chunk_files)


def process_audio(input_file, chunk_length_ms=60000, num_threads=5):
    output_dir = "chunks"
    chunk_files = ""
    with io.StringIO() as stdout, io.StringIO() as stderr, redirect_stdout(stdout), redirect_stderr(stderr):
        chunks = split_audio(input_file, chunk_length_ms, output_dir)

        chunk_groups = [chunks[i::num_threads] for i in range(num_threads)]
        chunk_indices_groups = [list(range(i, len(chunks), num_threads)) for i in range(num_threads)]

        result_queue = Queue()
        threads = []

        for chunk_group, chunk_indices_group in zip(chunk_groups, chunk_indices_groups):
            thread = threading.Thread(target=recognize_speech_from_chunk,
                                      args=(chunk_group, chunk_indices_group, result_queue))
            chunk_files = chunk_group
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        sorted_results = [None] * len(chunks)
        while not result_queue.empty():
            index, text = result_queue.get()
            sorted_results[index] = text

        full_text = " ".join(filter(None, sorted_results))
    return full_text, chunk_files


def convert_to_mono(input_audio, output_audio):
    sound = AudioSegment.from_file(input_audio)
    mono_sound = sound.set_channels(1)
    mono_sound.export(output_audio, format="wav")


def download_video_as_wav(url, output_file="audio"):
    import yt_dlp
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
