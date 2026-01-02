"""
Core Utilities - Day 04
Enhanced utility functions with better error handling
"""

import os
import re
import shutil
from pathlib import Path

def setup_directories():
    """Create necessary directories if they don't exist"""
    directories = ['output', 'temp', '.cache']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"Directory ready: {directory}")

def validate_url(url):
    """Enhanced URL validation for YouTube"""
    if not url:
        return False
    
    youtube_pattern = r'(youtube\.com|youtu\.be)'
    return bool(re.search(youtube_pattern, url))

def clean_temp_files():
    """Clean temporary files"""
    temp_dir = Path("temp")
    if temp_dir.exists():
        for file in temp_dir.glob("*"):
            if file.is_file():
                file.unlink()
        print("Temp files cleaned")

def get_video_id(url):
    """Extract video ID from YouTube URL"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def get_file_size(file_path):
    """Get file size in MB"""
    try:
        size_bytes = Path(file_path).stat().st_size
        return size_bytes / (1024 * 1024)  # Convert to MB
    except:
        return 0

class Config:
    """Enhanced configuration class"""
    
    OUTPUT_DIR = "output"
    TEMP_DIR = "temp"
    CACHE_DIR = ".cache"
    
    # Audio settings
    AUDIO_SAMPLE_RATE = 16000
    AUDIO_CHANNELS = 1
    AUDIO_BITRATE = "128k"
    
    # Video settings
    VIDEO_FORMAT = "mp4"
    AUDIO_FORMAT = "wav"
    
    # Download settings
    MAX_FILE_SIZE = 500  # MB
    CHUNK_SIZE = 8192

class YouTubeError(Exception):
    """Custom exception for YouTube-related errors"""
    pass

class AudioError(Exception):
    """Custom exception for audio processing errors"""
    pass

class MediaError(Exception):
    """Custom exception for media processing errors"""
    pass
