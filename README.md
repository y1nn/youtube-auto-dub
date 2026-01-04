# YouTube Auto Dub - Day 06

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
Day 06: Enhanced audio processing and file handling.

## New Features
- **Enhanced Audio Processing**: Audio chunking, normalization, and merging
- **Better File Handling**: Unique filename generation, progress saving/loading
- **Retry Logic**: Automatic retry for failed downloads and processing
- **Audio Pipeline**: Complete audio processing workflow with chunking
- **Improved Error Handling**: Custom exceptions for all error types
- **Progress Tracking**: Save and resume processing progress
- **Duration Formatting**: Human-readable duration display

## Key Components
- `media.py`: Enhanced audio/video processing with chunking and merging
- `core_utils.py`: Better file handling and progress tracking
- `youtube.py`: Retry logic and thumbnail downloading
- `engines.py`: Enhanced translation with text chunking
- `main.py`: Complete audio processing pipeline

## Audio Processing Pipeline
1. Download audio from YouTube
2. Extract audio information
3. Split audio into 30-second chunks
4. Transcribe each chunk
5. Combine transcriptions
6. Translate full text
7. Synthesize translated speech

## File Management
- Automatic temp file cleanup
- Unique filename generation with timestamps
- Progress saving to JSON files
- File size validation and monitoring

## Error Handling
- Retry logic for network operations
- Custom exceptions for different error types
- Graceful fallbacks for failed operations
- Detailed error logging

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
- requests: HTTP requests and translation API
- edge-tts: Text-to-speech synthesis
- numpy: Array processing
- librosa: Audio analysis
- ffmpeg-python: FFmpeg Python bindings
- tqdm: Progress bars
- colorama: Colored terminal output

## Next Steps
- Implement actual speech-to-text with Faster-Whisper
- Add real speaker diarization with Pyannote
- Implement audio separation with Demucs
- Add video reconstruction pipeline
- Add GUI interface
- Implement batch processing
