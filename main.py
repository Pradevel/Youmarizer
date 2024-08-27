from colorama import Fore, Style

from audio_processing import download_video_as_wav, process_audio
from speech_recognition import extract_keypoints
from text_processing import summarize_text, print_with_scroll


def main():
    video_url = input(Fore.CYAN + "Enter the YouTube video URL: " + Style.RESET_ALL)
    output_file = 'audio.wav'

    print(Fore.GREEN + "Downloading video..." + Style.RESET_ALL)
    download_video_as_wav(video_url)

    print(Fore.GREEN + "Processing audio..." + Style.RESET_ALL)
    text = process_audio(output_file, chunk_length_ms=60000, num_threads=5)

    print(Fore.GREEN + "Transcription complete. Generating summary..." + Style.RESET_ALL)
    summary = summarize_text(text)

    print_with_scroll(Fore.WHITE + summary + Style.RESET_ALL)

    print(Fore.GREEN + "Extracting key points..." + Style.RESET_ALL)
    keyphrases = extract_keypoints(summary)

    print(Fore.GREEN + "Key Points:" + Style.RESET_ALL)
    for point in keyphrases.split('. '):
        print(Fore.CYAN + f"• {point.strip()}" + Style.RESET_ALL)


if __name__ == "__main__":
    main()
