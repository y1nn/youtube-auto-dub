"""
Media Processing Module - Day 04
Basic audio and video processing functionality
"""

import os
import subprocess
from pathlib import Path
from core_utils import AudioError, MediaError, Config

class AudioProcessor:
    """Basic audio processing functionality"""
    
    def __init__(self):
        self.sample_rate = Config.AUDIO_SAMPLE_RATE
        self.channels = Config.AUDIO_CHANNELS
    
    def extract_audio(self, video_file):
        """Extract audio from video file"""
        try:
            output_file = os.path.join(
                Config.TEMP_DIR, 
                f"extracted_audio.{Config.AUDIO_FORMAT}"
            )
            
            # Use ffmpeg to extract audio
            cmd = [
                'ffmpeg', '-i', video_file,
                '-ar', str(self.sample_rate),
                '-ac', str(self.channels),
                '-y', output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and Path(output_file).exists():
                print(f"Audio extracted successfully: {output_file}")
                return output_file
            else:
                print(f"FFmpeg error: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"Error extracting audio: {e}")
            return None
    
    def convert_format(self, input_file, output_format):
        """Convert audio to different format"""
        try:
            input_path = Path(input_file)
            output_file = input_path.with_suffix(f'.{output_format}')
            
            cmd = ['ffmpeg', '-i', str(input_path), '-y', str(output_file)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and output_file.exists():
                return str(output_file)
            else:
                return None
                
        except Exception as e:
            print(f"Error converting format: {e}")
            return None
    
    def get_audio_info(self, audio_file):
        """Get basic audio information"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(audio_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                import json
                info = json.loads(result.stdout)
                
                for stream in info.get('streams', []):
                    if stream.get('codec_type') == 'audio':
                        return {
                            'duration': float(stream.get('duration', 0)),
                            'sample_rate': stream.get('sample_rate'),
                            'channels': stream.get('channels'),
                            'codec': stream.get('codec_name')
                        }
            
            return None
            
        except Exception as e:
            print(f"Error getting audio info: {e}")
            return None

class VideoProcessor:
    """Basic video processing functionality"""
    
    def __init__(self):
        pass
    
    def get_video_info(self, video_file):
        """Get basic video information"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(video_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                import json
                info = json.loads(result.stdout)
                
                video_stream = None
                audio_stream = None
                
                for stream in info.get('streams', []):
                    if stream.get('codec_type') == 'video' and not video_stream:
                        video_stream = stream
                    elif stream.get('codec_type') == 'audio' and not audio_stream:
                        audio_stream = stream
                
                return {
                    'duration': float(info.get('format', {}).get('duration', 0)),
                    'size': int(info.get('format', {}).get('size', 0)),
                    'video': {
                        'width': video_stream.get('width') if video_stream else 0,
                        'height': video_stream.get('height') if video_stream else 0,
                        'fps': eval(video_stream.get('r_frame_rate', '0/1')) if video_stream else 0,
                        'codec': video_stream.get('codec_name') if video_stream else None
                    },
                    'audio': {
                        'sample_rate': audio_stream.get('sample_rate') if audio_stream else 0,
                        'channels': audio_stream.get('channels') if audio_stream else 0,
                        'codec': audio_stream.get('codec_name') if audio_stream else None
                    }
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
    
    def extract_frames(self, video_file, output_dir, interval=1):
        """Extract frames from video at specified interval"""
        try:
            output_pattern = os.path.join(output_dir, "frame_%04d.jpg")
            
            cmd = [
                'ffmpeg', '-i', video_file,
                '-vf', f'fps=1/{interval}',
                '-y', output_pattern
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True
            else:
                print(f"Error extracting frames: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error extracting frames: {e}")
            return False
