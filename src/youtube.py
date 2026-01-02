"""
YouTube Module - Day 04
Enhanced YouTube video downloading functionality
"""

import yt_dlp
import os
from pathlib import Path
from core_utils import YouTubeError, Config, get_file_size

class YouTubeDownloader:
    """Enhanced YouTube video downloader"""
    
    def __init__(self):
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'outtmpl': os.path.join(Config.TEMP_DIR, '%(title)s.%(ext)s'),
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
                }
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
    
    def download_audio(self, url, output_path=None):
        """Download audio from YouTube video"""
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
            print(f"Error downloading audio: {e}")
            return None
    
    def download_video(self, url, output_path=None):
        """Download video from YouTube"""
        try:
            opts = self.ydl_opts.copy()
            opts['format'] = 'best[ext=mp4]/best'
            
            if output_path:
                opts['outtmpl'] = output_path
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)
                
        except Exception as e:
            print(f"Error downloading video: {e}")
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
                            'filesize': fmt.get('filesize')
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
