"""
Media Processing Module - Day 06
Enhanced audio and video processing with better file handling
"""

import os
import subprocess
import json
from pathlib import Path
from core_utils import AudioError, MediaError, Config, format_duration, FileError

class AudioProcessor:
    """Enhanced audio processing functionality"""
    
    def __init__(self):
        self.sample_rate = Config.AUDIO_SAMPLE_RATE
        self.channels = Config.AUDIO_CHANNELS
        self.chunk_duration = Config.AUDIO_CHUNK_DURATION
    
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
        """Get detailed audio information"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(audio_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                info = json.loads(result.stdout)
                
                for stream in info.get('streams', []):
                    if stream.get('codec_type') == 'audio':
                        duration = float(stream.get('duration', 0))
                        return {
                            'duration': duration,
                            'duration_formatted': format_duration(duration),
                            'sample_rate': stream.get('sample_rate'),
                            'channels': stream.get('channels'),
                            'codec': stream.get('codec_name'),
                            'bit_rate': stream.get('bit_rate'),
                            'size': int(info.get('format', {}).get('size', 0))
                        }
            
            return None
            
        except Exception as e:
            print(f"Error getting audio info: {e}")
            return None
    
    def split_audio(self, audio_file, chunk_duration=None):
        """Split audio into chunks with better error handling"""
        if chunk_duration is None:
            chunk_duration = self.chunk_duration
            
        try:
            # Get audio info first
            audio_info = self.get_audio_info(audio_file)
            if not audio_info:
                print(f"Could not get audio info for {audio_file}")
                return []
            
            duration = audio_info['duration']
            if duration <= chunk_duration:
                print(f"Audio is shorter than chunk duration ({duration}s <= {chunk_duration}s)")
                return [audio_file]
            
            output_pattern = os.path.join(Config.TEMP_DIR, "chunk_%04d.wav")
            
            cmd = [
                'ffmpeg', '-i', audio_file,
                '-f', 'segment',
                '-segment_time', str(chunk_duration),
                '-acodec', 'copy',
                '-y', output_pattern
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Return list of chunk files
                chunks = list(Path(Config.TEMP_DIR).glob("chunk_*.wav"))
                chunk_files = [str(chunk) for chunk in sorted(chunks)]
                
                print(f"Audio split into {len(chunk_files)} chunks")
                return chunk_files
            else:
                print(f"Error splitting audio: {result.stderr}")
                return []
                
        except Exception as e:
            print(f"Error splitting audio: {e}")
            return []
    
    def merge_audio_files(self, audio_files, output_file):
        """Merge multiple audio files into one"""
        try:
            if not audio_files:
                raise AudioError("No audio files to merge")
            
            if len(audio_files) == 1:
                return audio_files[0]
            
            # Create input list for ffmpeg
            input_args = []
            for audio_file in audio_files:
                input_args.extend(['-i', audio_file])
            
            # Filter to concatenate inputs
            filter_complex = f"concat=n={len(audio_files)}:v=0:a=1[out]"
            
            cmd = ['ffmpeg'] + input_args + [
                '-filter_complex', filter_complex,
                '-map', '[out]',
                '-y', output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and Path(output_file).exists():
                print(f"Audio files merged successfully: {output_file}")
                return output_file
            else:
                print(f"Error merging audio: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"Error merging audio files: {e}")
            return None
    
    def normalize_audio(self, audio_file, output_file=None):
        """Normalize audio levels"""
        try:
            if output_file is None:
                output_file = os.path.join(Config.TEMP_DIR, f"normalized_{Path(audio_file).name}")
            
            cmd = [
                'ffmpeg', '-i', audio_file,
                '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',
                '-y', output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and Path(output_file).exists():
                print(f"Audio normalized: {output_file}")
                return output_file
            else:
                print(f"Error normalizing audio: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"Error normalizing audio: {e}")
            return None

class VideoProcessor:
    """Enhanced video processing functionality"""
    
    def __init__(self):
        pass
    
    def get_video_info(self, video_file):
        """Get detailed video information"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(video_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                info = json.loads(result.stdout)
                
                video_stream = None
                audio_stream = None
                
                for stream in info.get('streams', []):
                    if stream.get('codec_type') == 'video' and not video_stream:
                        video_stream = stream
                    elif stream.get('codec_type') == 'audio' and not audio_stream:
                        audio_stream = stream
                
                duration = float(info.get('format', {}).get('duration', 0))
                
                return {
                    'duration': duration,
                    'duration_formatted': format_duration(duration),
                    'size': int(info.get('format', {}).get('size', 0)),
                    'size_mb': int(info.get('format', {}).get('size', 0)) / (1024 * 1024),
                    'video': {
                        'width': video_stream.get('width') if video_stream else 0,
                        'height': video_stream.get('height') if video_stream else 0,
                        'fps': eval(video_stream.get('r_frame_rate', '0/1')) if video_stream else 0,
                        'codec': video_stream.get('codec_name') if video_stream else None,
                        'bit_rate': video_stream.get('bit_rate')
                    },
                    'audio': {
                        'sample_rate': audio_stream.get('sample_rate') if audio_stream else 0,
                        'channels': audio_stream.get('channels') if audio_stream else 0,
                        'codec': audio_stream.get('codec_name') if audio_stream else None,
                        'bit_rate': audio_stream.get('bit_rate')
                    }
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
    
    def extract_frames(self, video_file, output_dir, interval=1):
        """Extract frames from video at specified interval"""
        try:
            Path(output_dir).mkdir(exist_ok=True)
            output_pattern = os.path.join(output_dir, "frame_%04d.jpg")
            
            cmd = [
                'ffmpeg', '-i', video_file,
                '-vf', f'fps=1/{interval}',
                '-y', output_pattern
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                frame_count = len(list(Path(output_dir).glob("frame_*.jpg")))
                print(f"Extracted {frame_count} frames")
                return True
            else:
                print(f"Error extracting frames: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error extracting frames: {e}")
            return False
    
    def merge_audio_video(self, video_file, audio_file, output_file):
        """Merge audio with video"""
        try:
            cmd = [
                'ffmpeg', '-i', video_file, '-i', audio_file,
                '-c:v', 'copy', '-c:a', 'aac',
                '-y', output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and Path(output_file).exists():
                print(f"Audio and video merged: {output_file}")
                return output_file
            else:
                print(f"Error merging audio and video: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"Error merging audio and video: {e}")
            return None
    
    def create_video_with_audio(self, audio_file, output_file, width=1280, height=720):
        """Create a simple video with audio and black background"""
        try:
            cmd = [
                'ffmpeg', '-f', 'lavfi', '-i', f'color=c=black:s={width}x{height}:d={self.get_audio_duration(audio_file)}',
                '-i', audio_file,
                '-c:v', 'libx264', '-c:a', 'aac',
                '-shortest', '-y', output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and Path(output_file).exists():
                print(f"Video created with audio: {output_file}")
                return output_file
            else:
                print(f"Error creating video: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"Error creating video with audio: {e}")
            return None
    
    def get_audio_duration(self, audio_file):
        """Get audio duration using ffprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return float(result.stdout.strip())
            
            return 0
            
        except:
            return 0
