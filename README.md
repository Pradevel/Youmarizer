# Youmarizer

Youmarizer is a Python application that extracts and summarizes content from YouTube videos. The application performs the following tasks:
1. **Downloads** the video as an audio file.
2. **Processes** the audio to transcribe spoken content.
3. **Summarizes** the transcribed text.
4. **Extracts key points** from the summary.

## Features

- **Download** YouTube videos and convert them to audio.
- **Split** audio into manageable chunks for transcription.
- **Transcribe** audio using the Vosk speech recognition model.
- **Summarize** the transcribed text using a transformer-based summarization model.
- **Extract** and display key points from the summary.

## Requirements

- Python 3.x
- Required Python libraries:
  - `yt-dlp`
  - `pydub`
  - `tqdm`
  - `vosk`
  - `transformers`
  - `colorama`

You can install the necessary libraries using pip:

```bash
pip install yt-dlp pydub tqdm vosk transformers colorama
```
### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/youmarizer.git
   ```
2.	**Install ffmpeg**:
Ensure that ffmpeg is installed on your system. You can download it from FFmpeg’s official website and follow the installation instructions for your operating system.
	
3.	**Download the Vosk model**:
Download the Vosk model from here and extract it to a directory named vosk-model-small-en-us-0.15 within your project folder.
	
4.	**Install Python dependencies**:
Make sure you have all the required libraries installed by running:

### Usage
1.	**Run the application**:
Execute the main.py script

    python main.py

2.	**Enter the YouTube video** URL when prompted:
    
```Enter the YouTube video URL:```

3.	**View the results**:
        - The summary will be displayed, and you will be prompted to press Enter to continue.
        - Key points extracted from the summary will be displayed with bullet points.
``
### Project Structure
- **main.py**: The main script to run the application.
- **audio_processor.py**: Contains functions for downloading, splitting, and processing audio.
- **transcriber.py**: Contains functions for speech recognition and transcription.
- **summarizer.py**: Contains functions for text summarization and key point extraction.
### Notes
- Ensure you have ffmpeg installed for audio processing. You can download it from FFmpeg’s official website.
- Adjust the chunk_length_ms parameter in process_audio if you encounter performance issues or need finer control over chunk sizes.

### Troubleshooting
- Error: ffmpeg not found: Make sure ffmpeg is installed and added to your system’s PATH.
- Model not found: Verify that the Vosk model is correctly downloaded and extracted in the specified directory.

### License
This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.