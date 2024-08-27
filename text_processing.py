from transformers import pipeline
from colorama import Fore, Style

summarizer = pipeline("summarization")

def summarize_text(text, max_chunk_length=1024):
    def split_text(text, max_length):
        return [text[i:i + max_length] for i in range(0, len(text), max_length)]

    chunks = split_text(text, max_chunk_length)
    summaries = []
    for chunk in chunks:
        summary = summarizer(chunk, max_length=50, min_length=30, do_sample=False)
        summaries.append(summary[0]['summary_text'])

    full_summary = " ".join(summaries)
    return full_summary

def print_with_scroll(text):
    print(Fore.YELLOW + "Summary:" + Style.RESET_ALL)
    for line in text.split('\n'):
        print(line)
    input("Press Enter to continue...")