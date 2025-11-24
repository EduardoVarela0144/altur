"""
Speech-to-Text Service using Whisper
"""
import os
import whisper
from typing import Optional


class STTService:
    """Service for transcribing audio files using Whisper"""
    
    def __init__(self, model_name: str = "base"):
        """
        Initialize the STT service with a Whisper model
        
        Args:
            model_name: Whisper model name (tiny, base, small, medium, large)
        """
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model (lazy loading)"""
        if self.model is None:
            print(f"[STT] Loading Whisper model: {self.model_name}")
            try:
                self.model = whisper.load_model(self.model_name)
                print(f"[STT] ✅ Model loaded successfully")
            except Exception as e:
                print(f"[STT] ❌ Error loading model: {e}")
                raise
    
    def transcribe(self, audio_path: str, language: Optional[str] = None) -> str:
        """
        Transcribe an audio file to text
        
        Args:
            audio_path: Path to the audio file
            language: Language code (e.g., 'en', 'es'). If None, auto-detect
            
        Returns:
            str: Transcribed text
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            print(f"[STT] Transcribing: {audio_path} (this may take a moment...)")
            # Optimize transcription for speed
            # verbose=False: Reduce logging overhead
            # condition_on_previous_text=False: Faster but slightly less accurate
            # fp16=False: Use FP32 for CPU compatibility
            # beam_size=1: Use greedy decoding instead of beam search (much faster)
            result = self.model.transcribe(
                audio_path,
                language=language,
                verbose=False,
                condition_on_previous_text=False,
                fp16=False,  # Explicitly set for CPU
                beam_size=1,  # Use greedy decoding (faster than beam search)
                best_of=1,  # Don't generate multiple candidates
                task="transcribe"
            )
            transcript = result["text"].strip()
            print(f"[STT] ✅ Transcription completed ({len(transcript)} characters)")
            return transcript
        except Exception as e:
            print(f"[STT] ❌ Error transcribing audio: {e}")
            raise


# Global instance
_stt_service = None

def get_stt_service(model_name: str = None) -> STTService:
    """Get or create the global STT service instance"""
    global _stt_service
    if _stt_service is None:
        model = model_name or os.getenv("WHISPER_MODEL", "base")
        _stt_service = STTService(model_name=model)
    return _stt_service

