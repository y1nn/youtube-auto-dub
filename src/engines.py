"""
Engines Module - Day 06
Enhanced translation and TTS engines with better error handling
"""

import requests
import json
import os
import time
from pathlib import Path
from core_utils import Config, TranslationError, TTSError

class TranslationEngine:
    """Enhanced translation engine with retry logic"""
    
    def __init__(self):
        self.supported_languages = {
            'en': 'English',
            'es': 'Spanish', 
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'vi': 'Vietnamese'
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def translate(self, text, target_language, source_language='en'):
        """Translate text to target language with retry logic"""
        if not text or not text.strip():
            return ""
        
        if target_language not in self.supported_languages:
            raise TranslationError(f"Unsupported target language: {target_language}")
        
        # Split long text into chunks
        max_chunk_size = 5000  # Google Translate limit
        text_chunks = self._split_text(text, max_chunk_size)
        
        translated_chunks = []
        
        for chunk in text_chunks:
            for attempt in range(Config.RETRY_ATTEMPTS):
                try:
                    translated_chunk = self._translate_chunk(chunk, target_language, source_language)
                    if translated_chunk:
                        translated_chunks.append(translated_chunk)
                        break
                    else:
                        # Fallback to original text
                        translated_chunks.append(chunk)
                        break
                        
                except Exception as e:
                    print(f"Translation attempt {attempt + 1} failed: {e}")
                    if attempt < Config.RETRY_ATTEMPTS - 1:
                        time.sleep(Config.RETRY_DELAY)
                    else:
                        print(f"Failed to translate after {Config.RETRY_ATTEMPTS} attempts")
                        translated_chunks.append(chunk)
        
        return ' '.join(translated_chunks)
    
    def _translate_chunk(self, text, target_language, source_language):
        """Translate a single chunk of text"""
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                'client': 'gtx',
                'sl': source_language,
                'tl': target_language,
                'dt': 't',
                'q': text
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result and len(result) > 0 and result[0]:
                    translated_text = ''.join([item[0] for item in result[0] if item[0]])
                    return translated_text
                else:
                    return text
            else:
                print(f"Translation API error: {response.status_code}")
                return text
                
        except Exception as e:
            print(f"Translation error: {e}")
            return text
    
    def _split_text(self, text, max_size):
        """Split text into chunks of maximum size"""
        if len(text) <= max_size:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        # Split by sentences to maintain context
        sentences = text.split('. ')
        
        for sentence in sentences:
            if len(current_chunk + sentence) <= max_size:
                current_chunk += sentence + '. '
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + '. '
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def detect_language(self, text):
        """Detect language of text"""
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                'client': 'gtx',
                'sl': 'auto',
                'dt': 't',
                'q': text[:100]  # Use first 100 chars for detection
            }
            
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                result = response.json()
                if result and len(result) > 2:
                    return result[2]
            
            return 'en'  # Default to English
            
        except Exception as e:
            print(f"Language detection error: {e}")
            return 'en'

class TTSEngine:
    """Enhanced text-to-speech engine"""
    
    def __init__(self):
        self.supported_voices = {
            'en': {'male': 'en-US-GuyNeural', 'female': 'en-US-JennyNeural'},
            'es': {'male': 'es-ES-AlvaroNeural', 'female': 'es-ES-ElviraNeural'},
            'fr': {'male': 'fr-FR-DenysNeural', 'female': 'fr-FR-DeniseNeural'},
            'de': {'male': 'de-DE-ConradNeural', 'female': 'de-DE-KatjaNeural'},
            'it': {'male': 'it-IT-DiegoNeural', 'female': 'it-IT-ElsaNeural'},
            'pt': {'male': 'pt-BR-AntonioNeural', 'female': 'pt-BR-FranciscaNeural'},
            'zh': {'male': 'zh-CN-YunxiNeural', 'female': 'zh-CN-XiaoxiaoNeural'},
            'ja': {'male': 'ja-JP-KeitaNeural', 'female': 'ja-JP-NanamiNeural'},
            'ko': {'male': 'ko-KR-InJoonNeural', 'female': 'ko-KR-SunHiNeural'},
            'vi': {'male': 'vi-VN-NamMinhNeural', 'female': 'vi-VN-HoaiMyNeural'}
        }
    
    def synthesize(self, text, language, voice='female'):
        """Synthesize speech from text with better error handling"""
        try:
            if not text or not text.strip():
                raise TTSError("Empty text for synthesis")
            
            if language not in self.supported_voices:
                raise TTSError(f"Unsupported language: {language}")
            
            if voice not in self.supported_voices[language]:
                voice = 'female'  # Default to female voice
            
            voice_name = self.supported_voices[language][voice]
            
            # Create output filename
            timestamp = int(time.time())
            output_file = os.path.join(Config.TEMP_DIR, f"tts_{language}_{voice}_{timestamp}.wav")
            
            # For now, create a placeholder audio file
            # In real implementation, this would use edge-tts library
            with open(output_file, 'wb') as f:
                # Write a simple WAV header and placeholder data
                f.write(b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x40\x1f\x00\x00\x80\x3e\x00\x00\x02\x00\x10\x00data\x00\x08\x00\x00')
                f.write(b'\x00' * 1000)  # Placeholder audio data
            
            print(f"TTS synthesized: {text[:50]}... in {language} ({voice})")
            return output_file
            
        except Exception as e:
            print(f"TTS error: {e}")
            return None
    
    def get_available_voices(self, language):
        """Get available voices for language"""
        return list(self.supported_voices.get(language, {}).keys())
    
    def synthesize_long_text(self, text, language, voice='female', max_chunk_size=1000):
        """Synthesize long text by splitting into chunks"""
        if not text or not text.strip():
            return []
        
        # Split text into sentences
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) <= max_chunk_size:
                current_chunk += sentence + '. '
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + '. '
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Synthesize each chunk
        audio_files = []
        for i, chunk in enumerate(chunks):
            print(f"Synthesizing chunk {i+1}/{len(chunks)}")
            audio_file = self.synthesize(chunk, language, voice)
            if audio_file and Path(audio_file).exists():
                audio_files.append(audio_file)
        
        return audio_files

class STTEngine:
    """Enhanced speech-to-text engine"""
    
    def __init__(self):
        self.supported_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'zh', 'ja', 'ko', 'vi']
    
    def transcribe(self, audio_file, language='en'):
        """Transcribe audio to text with better error handling"""
        try:
            if not Path(audio_file).exists():
                print(f"Audio file not found: {audio_file}")
                return ""
            
            print(f"Transcribing {audio_file} in {language}")
            
            # Placeholder transcription
            # In real implementation, this would use faster-whisper
            filename = Path(audio_file).name
            placeholder_text = f"This is a placeholder transcription of {filename} in {language}. "
            placeholder_text += "The actual implementation would use faster-whisper to convert speech to text accurately."
            
            return placeholder_text
            
        except Exception as e:
            print(f"STT error: {e}")
            return ""
    
    def transcribe_with_timestamps(self, audio_file, language='en'):
        """Transcribe audio with timestamps - placeholder"""
        try:
            transcription = self.transcribe(audio_file, language)
            
            # Placeholder with simple timestamps
            return [
                {
                    'start': 0,
                    'end': 10,
                    'text': transcription[:len(transcription)//2],
                    'confidence': 0.9
                },
                {
                    'start': 10,
                    'end': 20,
                    'text': transcription[len(transcription)//2:],
                    'confidence': 0.85
                }
            ]
            
        except Exception as e:
            print(f"STT with timestamps error: {e}")
            return []

class DiarizationEngine:
    """Enhanced speaker diarization engine"""
    
    def __init__(self):
        pass
    
    def segment_speakers(self, audio_file):
        """Segment audio by speakers - placeholder"""
        try:
            if not Path(audio_file).exists():
                print(f"Audio file not found: {audio_file}")
                return []
            
            print(f"Segmenting speakers in {audio_file}")
            
            # Placeholder diarization
            # In real implementation, this would use pyannote.audio
            segments = [
                {'start': 0, 'end': 5, 'speaker': 'speaker_0', 'confidence': 0.9},
                {'start': 5, 'end': 10, 'speaker': 'speaker_1', 'confidence': 0.85},
                {'start': 10, 'end': 15, 'speaker': 'speaker_0', 'confidence': 0.88}
            ]
            
            return segments
            
        except Exception as e:
            print(f"Diarization error: {e}")
            return []
