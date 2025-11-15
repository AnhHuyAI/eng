# app/services/stt_service.py

from google.cloud import speech_v1p1beta1 as speech
from flask import current_app
import io

class SpeechToTextService:
    """Service for Google Speech-to-Text API"""
    
    def __init__(self):
        # Initialize Google Cloud Speech client
        # Note: Requires GOOGLE_APPLICATION_CREDENTIALS environment variable
        # pointing to service account JSON file
        self.client = speech.SpeechClient()
    
    def transcribe_audio(self, audio_file_path):
        """
        Transcribe audio file to text
        Returns: (transcript, confidence, cost_usd)
        """
        try:
            # Read audio file
            with io.open(audio_file_path, 'rb') as audio_file:
                content = audio_file.read()
            
            audio = speech.RecognitionAudio(content=content)
            
            # Configure recognition
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code='en-US',
                enable_automatic_punctuation=True,
                enable_word_time_offsets=False,
                model='default',
                use_enhanced=True,  # Better accuracy
            )
            
            # Perform transcription
            response = self.client.recognize(config=config, audio=audio)
            
            # Extract transcript
            transcript = ""
            confidence = 0.0
            
            for result in response.results:
                transcript += result.alternatives[0].transcript + " "
                confidence += result.alternatives[0].confidence
            
            if response.results:
                confidence = confidence / len(response.results)
            
            transcript = transcript.strip()
            
            # Calculate cost (Google STT pricing: $0.024 per minute)
            # Estimate duration from audio file size (rough estimate)
            audio_size_mb = len(content) / (1024 * 1024)
            estimated_minutes = audio_size_mb / 0.5  # Rough: 0.5MB per minute
            cost_usd = estimated_minutes * 0.024
            
            return transcript, confidence, cost_usd
            
        except Exception as e:
            current_app.logger.error(f"STT error: {str(e)}")
            raise Exception(f"Speech-to-Text error: {str(e)}")
    
    def transcribe_audio_long(self, audio_file_path):
        """
        Transcribe long audio file (>1 minute) using long_running_recognize
        For future implementation if needed
        """
        # TODO: Implement long audio transcription
        pass


# Alternative: Use OpenAI Whisper API (cheaper option)
class WhisperSTTService:
    """Alternative STT using OpenAI Whisper API"""
    
    def __init__(self):
        import openai
        self.client = openai.OpenAI(api_key=current_app.config.get('OPENAI_API_KEY'))
    
    def transcribe_audio(self, audio_file_path):
        """
        Transcribe using Whisper API
        Pricing: $0.006 per minute (4x cheaper than Google)
        """
        try:
            with open(audio_file_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"
                )
            
            # Estimate cost
            import os
            audio_size_mb = os.path.getsize(audio_file_path) / (1024 * 1024)
            estimated_minutes = audio_size_mb / 0.5
            cost_usd = estimated_minutes * 0.006
            
            return transcript.text, 0.95, cost_usd  # Assume 95% confidence
            
        except Exception as e:
            current_app.logger.error(f"Whisper STT error: {str(e)}")
            raise Exception(f"Speech-to-Text error: {str(e)}")


# Lazy initialization
_stt_service = None

def get_stt_service():
    """Get or create STT service instance"""
    global _stt_service
    if _stt_service is None:
        _stt_service = WhisperSTTService()  # OpenAI Whisper (recommended for cost)
        # Alternative: _stt_service = SpeechToTextService()  # Google
    return _stt_service

# For backward compatibility
def stt_service():
    return get_stt_service()