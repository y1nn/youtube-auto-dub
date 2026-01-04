"""
Core Utilities - Day 06
Enhanced utility functions with better file handling
"""

import os
import re
import shutil
import json
import time
from pathlib import Path
from datetime import datetime

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
        cleaned_count = 0
        for file in temp_dir.glob("*"):
            if file.is_file():
                file.unlink()
                cleaned_count += 1
        print(f"Cleaned {cleaned_count} temp files")

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

def generate_unique_filename(base_name, extension, directory="temp"):
    """Generate unique filename with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{base_name}_{timestamp}.{extension}"
    return os.path.join(directory, filename)

def save_progress(data, filename="progress.json"):
    """Save processing progress to file"""
    try:
        progress_file = os.path.join(Config.CACHE_DIR, filename)
        with open(progress_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Progress saved to {progress_file}")
    except Exception as e:
        print(f"Error saving progress: {e}")

def load_progress(filename="progress.json"):
    """Load processing progress from file"""
    try:
        progress_file = os.path.join(Config.CACHE_DIR, filename)
        if Path(progress_file).exists():
            with open(progress_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading progress: {e}")
    return None

def format_duration(seconds):
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

class Config:
    """Enhanced configuration class"""
    
    OUTPUT_DIR = "output"
    TEMP_DIR = "temp"
    CACHE_DIR = ".cache"
    
    # Audio settings
    AUDIO_SAMPLE_RATE = 16000
    AUDIO_CHANNELS = 1
    AUDIO_BITRATE = "128k"
    AUDIO_CHUNK_DURATION = 30  # seconds
    
    # Video settings
    VIDEO_FORMAT = "mp4"
    AUDIO_FORMAT = "wav"
    
    # Download settings
    MAX_FILE_SIZE = 500  # MB
    CHUNK_SIZE = 8192
    
    # Language settings
    DEFAULT_SOURCE_LANGUAGE = "en"
    DEFAULT_TARGET_LANGUAGE = "es"
    DEFAULT_VOICE = "female"
    
    # Processing settings
    MAX_CONCURRENT_CHUNKS = 4
    RETRY_ATTEMPTS = 3
    RETRY_DELAY = 2  # seconds

class YouTubeError(Exception):
    """Custom exception for YouTube-related errors"""
    pass

class AudioError(Exception):
    """Custom exception for audio processing errors"""
    pass

class MediaError(Exception):
    """Custom exception for media processing errors"""
    pass

class TranslationError(Exception):
    """Custom exception for translation errors"""
    pass

class TTSError(Exception):
    """Custom exception for TTS errors"""
    pass

class FileError(Exception):
    """Custom exception for file handling errors"""
    pass
