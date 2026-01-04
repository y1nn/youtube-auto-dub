"""
YouTube Module - Day 06
Enhanced YouTube video downloading with better error handling
"""

import yt_dlp
import os
import time
from pathlib import Path
from core_utils import YouTubeError, Config, get_file_size, generate_unique_filename

class YouTubeDownloader:
    """Enhanced YouTube video downloader"""
    
    def __init__(self):
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'outtmpl': os.path.join(Config.TEMP_DIR, '%(title)s.%(ext)s'),
            'retries': Config.RETRY_ATTEMPTS,
            'fragment_retries': Config.RETRY_ATTEMPTS,
        }
    
    def get_video_info(self, url):
        """Get detailed video information"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'upload_date': info.get('upload_date', 'Unknown'),
                    'description': info.get('description', ''),
                    'thumbnail': info.get('thumbnail', ''),
                    'id': info.get('id', ''),
                    'webpage_url': info.get('webpage_url', url),
                }
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
    
    def download_audio(self, url, output_path=None):
        """Download audio from YouTube video with retry logic"""
        for attempt in range(Config.RETRY_ATTEMPTS):
            try:
                opts = self.ydl_opts.copy()
                opts['format'] = 'bestaudio/best'
                opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
                
                if output_path:
                    opts['outtmpl'] = output_path
                else:
                    # Generate unique filename
                    video_id = self._extract_video_id(url)
                    opts['outtmpl'] = generate_unique_filename(f"audio_{video_id}", "mp3")
                
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    downloaded_file = ydl.prepare_filename(info)
                    
                    # Check if file was converted to mp3
                    if downloaded_file.endswith('.mp3'):
                        return downloaded_file
                    else:
                        # Return the converted file path
                        mp3_file = Path(downloaded_file).with_suffix('.mp3')
                        return str(mp3_file) if mp3_file.exists() else downloaded_file
                        
            except Exception as e:
                print(f"Download attempt {attempt + 1} failed: {e}")
                if attempt < Config.RETRY_ATTEMPTS - 1:
                    time.sleep(Config.RETRY_DELAY * (attempt + 1))
                else:
                    print(f"Failed to download audio after {Config.RETRY_ATTEMPTS} attempts")
                    return None
    
    def download_video(self, url, output_path=None):
        """Download video from YouTube with retry logic"""
        for attempt in range(Config.RETRY_ATTEMPTS):
            try:
                opts = self.ydl_opts.copy()
                opts['format'] = 'best[ext=mp4]/best'
                
                if output_path:
                    opts['outtmpl'] = output_path
                else:
                    video_id = self._extract_video_id(url)
                    opts['outtmpl'] = generate_unique_filename(f"video_{video_id}", "mp4")
                
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    return ydl.prepare_filename(info)
                    
            except Exception as e:
                print(f"Video download attempt {attempt + 1} failed: {e}")
                if attempt < Config.RETRY_ATTEMPTS - 1:
                    time.sleep(Config.RETRY_DELAY * (attempt + 1))
                else:
                    print(f"Failed to download video after {Config.RETRY_ATTEMPTS} attempts")
                    return None
    
    def get_available_formats(self, url):
        """Get available formats for the video"""
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = []
                
                for fmt in info.get('formats', []):
                    if fmt.get('vcodec') != 'none':  # Video formats
                        formats.append({
                            'format_id': fmt.get('format_id'),
                            'ext': fmt.get('ext'),
                            'quality': fmt.get('quality'),
                            'filesize': fmt.get('filesize'),
                            'fps': fmt.get('fps'),
                            'resolution': fmt.get('resolution'),
                        })
                
                return formats
        except Exception as e:
            print(f"Error getting formats: {e}")
            return []
    
    def check_file_size(self, url):
        """Check if video is within size limits"""
        try:
            info = self.get_video_info(url)
            if info and info.get('duration'):
                # Rough estimation: 1 minute = 2MB for audio
                estimated_size = (info['duration'] / 60) * 2
                return estimated_size <= Config.MAX_FILE_SIZE
            return True
        except:
            return True
    
    def _extract_video_id(self, url):
        """Extract video ID from URL"""
        from core_utils import get_video_id
        return get_video_id(url) or "unknown"
    
    def download_thumbnail(self, url, output_path=None):
        """Download video thumbnail"""
        try:
            video_info = self.get_video_info(url)
            if video_info and video_info.get('thumbnail'):
                import requests
                
                thumbnail_url = video_info['thumbnail']
                if output_path:
                    thumbnail_path = output_path
                else:
                    video_id = self._extract_video_id(url)
                    thumbnail_path = generate_unique_filename(f"thumb_{video_id}", "jpg")
                
                response = requests.get(thumbnail_url, stream=True)
                if response.status_code == 200:
                    with open(thumbnail_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return thumbnail_path
                
        except Exception as e:
            print(f"Error downloading thumbnail: {e}")
        
        return None
