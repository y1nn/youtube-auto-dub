#!/usr/bin/env python3
"""
YouTube Auto Dub - Day 06
Enhanced audio processing and file handling
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from core_utils import setup_directories, validate_url, get_video_id, Config, clean_temp_files
    from youtube import YouTubeDownloader
    from media import AudioProcessor, VideoProcessor
    from engines import TranslationEngine, TTSEngine, STTEngine, DiarizationEngine
except ImportError as e:
    print(f"Error: {e}")
    sys.exit(1)

def process_audio_pipeline(audio_file):
    """Complete audio processing pipeline"""
    print(f"Starting audio processing pipeline for: {audio_file}")
    
    # Initialize audio processor
    audio_processor = AudioProcessor()
    
    # Get audio info
    audio_info = audio_processor.get_audio_info(audio_file)
    if audio_info:
        print(f"Audio info: {audio_info}")
    
    # Split audio into chunks for better processing
    chunks = audio_processor.split_audio(audio_file, chunk_duration=30)
    print(f"Audio split into {len(chunks)} chunks")
    
    # Process each chunk
    transcriptions = []
    stt_engine = STTEngine()
    
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}: {chunk}")
        
        # Transcribe chunk
        transcription = stt_engine.transcribe(chunk, language='en')
        transcriptions.append({
            'chunk': i,
            'file': chunk,
            'text': transcription
        })
    
    # Combine transcriptions
    full_transcription = ' '.join([t['text'] for t in transcriptions])
    print(f"Full transcription: {full_transcription[:100]}...")
    
    return transcriptions, full_transcription

def main():
    print("YouTube Auto Dub - Starting...")
    
    # Setup directories
    setup_directories()
    
    # Clean old temp files
    clean_temp_files()
    
    # TODO: Get YouTube URL from user
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Placeholder
    
    # Validate URL
    if not validate_url(youtube_url):
        print("Invalid URL!")
        return
    
    print(f"Processing URL: {youtube_url}")
    
    # Initialize YouTube downloader
    downloader = YouTubeDownloader()
    
    # Get video info
    video_info = downloader.get_video_info(youtube_url)
    if video_info:
        print(f"Video found: {video_info.get('title', 'Unknown')}")
        print(f"Duration: {video_info.get('duration', 0)} seconds")
    else:
        print("Failed to get video info!")
        return
    
    # Download audio
    audio_file = downloader.download_audio(youtube_url)
    if audio_file and Path(audio_file).exists():
        print(f"Audio downloaded: {audio_file}")
        
        # Process audio through pipeline
        transcriptions, full_transcription = process_audio_pipeline(audio_file)
        
        if full_transcription:
            # Translate text
            translator = TranslationEngine()
            translated_text = translator.translate(full_transcription, 'es')
            print(f"Translation: {translated_text[:100]}...")
            
            # Synthesize speech
            tts_engine = TTSEngine()
            tts_audio = tts_engine.synthesize(translated_text, 'es', voice='female')
            if tts_audio and Path(tts_audio).exists():
                print(f"TTS audio created: {tts_audio}")
            else:
                print("Failed to create TTS audio!")
        else:
            print("Failed to transcribe audio!")
    else:
        print("Failed to download audio!")
        return
    
    # TODO: Implement video reconstruction
    print("YouTube Auto Dub - Finished!")

if __name__ == "__main__":
    main()
