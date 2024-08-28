import os
import threading
import io
from contextlib import redirect_stdout, redirect_stderr
from colorama import Fore, Style

from audio_processing import download_video_as_wav, process_audio
from speech_recognition import extract_keypoints
from text_processing import summarize_text, print_with_scroll

text = ''
summary = ''
keyphrases = ''
text = ''
chunk_files = ''
def run_with_suppressed_logs(func, *args, **kwargs):
    """Run a function with suppressed stdout and stderr logs."""
    with io.StringIO() as stdout, io.StringIO() as stderr, redirect_stdout(stdout), redirect_stderr(stderr):
        return func(*args, **kwargs)

def cleanup_files(audio_file, chunks_dir):
    if os.path.isfile(audio_file):
        os.remove(audio_file)
    if os.path.isdir(chunks_dir):
        for file in os.listdir(chunks_dir):
            file_path = os.path.join(chunks_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        os.rmdir(chunks_dir)



def main():
    video_url = input(Fore.CYAN + "Enter the YouTube video URL: " + Style.RESET_ALL)
    output_file = 'audio.wav'

    # Thread for downloading video
    def download_task():
        print(Fore.GREEN + "Downloading video..." + Style.RESET_ALL)
        run_with_suppressed_logs(download_video_as_wav, video_url)

    # Thread for processing audio
    def process_task():
        print(Fore.GREEN + "Processing audio..." + Style.RESET_ALL)
        global text
        global chunk_files
        text, chunk_files = run_with_suppressed_logs(process_audio, output_file, chunk_length_ms=60000, num_threads=5)

    # Thread for summarizing text
    def summarize_task():
        print(Fore.GREEN + "Transcription complete. Generating summary..." + Style.RESET_ALL)
        global summary
        summary = run_with_suppressed_logs(summarize_text, text)

    # Thread for extracting key points
    def extract_keypoints_task():
        print(Fore.GREEN + "Extracting key points..." + Style.RESET_ALL)
        global keyphrases
        keyphrases = run_with_suppressed_logs(extract_keypoints, summary)

    # Start threads
    download_thread = threading.Thread(target=download_task)
    process_thread = threading.Thread(target=process_task)
    summarize_thread = threading.Thread(target=summarize_task)
    extract_keypoints_thread = threading.Thread(target=extract_keypoints_task)

    download_thread.start()
    download_thread.join()

    process_thread.start()
    process_thread.join()

    summarize_thread.start()
    summarize_thread.join()

    extract_keypoints_thread.start()
    extract_keypoints_thread.join()

    print_with_scroll(Fore.WHITE + summary + Style.RESET_ALL)

    print(Fore.GREEN + "Key Points:" + Style.RESET_ALL)
    for point in keyphrases.split('. '):
        print(Fore.CYAN + f"• {point.strip()}" + Style.RESET_ALL)
    cleanup_files('audio.wav', 'chunks')


if __name__ == "__main__":
    main()