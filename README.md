# YouTube Auto Dub - Day 04

## Project Overview
YouTube Auto Dub is a tool to automatically dub YouTube videos into different languages.

## Features (Planned)
- YouTube video downloading
- Audio extraction and processing
- Speech-to-text transcription
- Text translation
- Voice synthesis
- Audio mixing and video reconstruction

## Current Status
Day 04: Enhanced YouTube downloading and basic media processing.

## New Features
- **Enhanced YouTube Downloader**: Real audio download with format conversion
- **Audio Processor**: Audio extraction and format conversion using FFmpeg
- **Video Processor**: Basic video information extraction
- **Engine Placeholders**: Framework for translation, TTS, STT, and diarization
- **Better Error Handling**: Custom exceptions and improved validation
- **File Management**: Enhanced file operations and size checking

## Key Components
- `youtube.py`: Enhanced YouTube video downloading
- `media.py`: Audio and video processing with FFmpeg
- `engines.py`: Placeholder classes for AI engines
- `core_utils.py`: Enhanced utilities with better error handling

## Installation
```bash
pip install -r requirements.txt
```

**Note**: Requires FFmpeg to be installed and available in PATH.

## Usage
```bash
python main.py
```

## Dependencies
- yt-dlp: YouTube video downloading
- requests: HTTP requests
- pathlib2: Enhanced path handling
- numpy: Array processing
- librosa: Audio analysis
- ffmpeg-python: FFmpeg Python bindings

## Next Steps
- Implement actual speech-to-text with Faster-Whisper
- Add real translation capabilities
- Implement TTS with Edge-TTS
- Add speaker diarization with Pyannote
- Implement audio separation with Demucs
