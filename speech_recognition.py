import io
import json
import wave
from contextlib import redirect_stdout, redirect_stderr

from vosk import Model, KaldiRecognizer

model_path = "./vosk-model-small-en-us-0.15"
model = Model(model_path)


def extract_keypoints(text, max_chunk_length=1024):
    from transformers import pipeline
    summarizer = pipeline("summarization")

    def split_text(text, max_length):
        return [text[i:i + max_length] for i in range(0, len(text), max_length)]

    chunks = split_text(text, max_chunk_length)
    keypoints = []
    for chunk in chunks:
        summary = summarizer(chunk, max_length=150, min_length=30, do_sample=False)
        keypoints.append(summary[0]['summary_text'])

    full_keypoints = " ".join(keypoints)
    return full_keypoints


def recognize_speech_from_chunk(chunk_files, chunk_indices, result_queue):
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
