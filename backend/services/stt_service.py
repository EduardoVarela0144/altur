"""
Speech-to-Text Service using Whisper
"""
import os
import whisper
import subprocess
from typing import Optional


class STTService:
    """Service for transcribing audio files using Whisper"""
    
    def __init__(self, model_name: str = "tiny"):
        """
        Initialize the STT service with a Whisper model
        
        Args:
            model_name: Whisper model name (tiny, base, small, medium, large)
            Default is 'tiny' for faster processing
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
    
    def _preprocess_audio(self, audio_path: str, max_duration: int = 180) -> str:
        """
        Preprocess audio to optimize for Whisper (16kHz mono WAV)
        Only preprocess if file is large or in non-optimal format
        
        Args:
            audio_path: Path to original audio file
            max_duration: Maximum duration in seconds to process (default: 3 minutes)
            
        Returns:
            str: Path to preprocessed audio file or original if preprocessing skipped
        """
        try:
            # Check file size - if small, skip preprocessing to save time
            file_size = os.path.getsize(audio_path)
            file_size_mb = file_size / (1024 * 1024)
            
            # Skip preprocessing for small files (< 5MB) to avoid overhead
            if file_size_mb < 5:
                print(f"[STT] Skipping preprocessing for small file ({file_size_mb:.2f}MB)")
                return audio_path
            
            # Create temporary file for preprocessed audio
            temp_dir = os.path.dirname(audio_path)
            preprocessed_path = os.path.join(temp_dir, f"preprocessed_{os.path.basename(audio_path)}.wav")
            
            # Use ffmpeg to convert to 16kHz mono WAV (Whisper's native format)
            # Limit duration to max_duration seconds to speed up processing
            # Use faster encoding settings
            cmd = [
                'ffmpeg',
                '-i', audio_path,
                '-ar', '16000',  # Sample rate: 16kHz (Whisper's native)
                '-ac', '1',      # Mono channel
                '-t', str(max_duration),  # Limit duration (3 minutes max for speed)
                '-c:a', 'pcm_s16le',  # Use PCM encoding (faster)
                '-y',            # Overwrite output file
                preprocessed_path
            ]
            
            # Run ffmpeg with timeout
            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                check=True,
                timeout=30  # Reduced timeout to 30 seconds
            )
            
            # Check if output file was created and has content
            if os.path.exists(preprocessed_path) and os.path.getsize(preprocessed_path) > 0:
                print(f"[STT] Audio preprocessed: {audio_path} -> {preprocessed_path}")
                return preprocessed_path
            else:
                print(f"[STT] ⚠️ Preprocessed file is empty, using original")
                return audio_path
        except subprocess.TimeoutExpired:
            print(f"[STT] ⚠️ Audio preprocessing timed out, using original file")
            return audio_path
        except subprocess.CalledProcessError as e:
            print(f"[STT] ⚠️ Audio preprocessing failed, using original file")
            return audio_path
        except Exception as e:
            print(f"[STT] ⚠️ Audio preprocessing error ({e}), using original file")
            return audio_path
    
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
            
            # Preprocess audio for faster transcription
            processed_audio = self._preprocess_audio(audio_path)
            cleanup_processed = processed_audio != audio_path
            
            try:
                # Optimized parameters for maximum speed
                result = self.model.transcribe(
                    processed_audio,
                    language=language,
                    verbose=False,
                    condition_on_previous_text=False,
                    fp16=False,  # Use FP32 for CPU compatibility
                    beam_size=1,  # Use greedy decoding (much faster than beam search)
                    best_of=1,  # Don't generate multiple candidates
                    task="transcribe",
                    # Additional speed optimizations
                    temperature=0,  # Deterministic, faster
                    compression_ratio_threshold=2.4,  # Skip if too compressed
                    logprob_threshold=-1.0,  # Skip low probability segments
                    no_speech_threshold=0.6,  # Skip silent segments faster
                    # Additional optimizations for speed
                    initial_prompt=None,  # No initial prompt (faster)
                    word_timestamps=False,  # Disable word timestamps (faster)
                )
                transcript = result["text"].strip()
                print(f"[STT] ✅ Transcription completed ({len(transcript)} characters)")
                return transcript
            finally:
                # Clean up preprocessed file if created
                if cleanup_processed and os.path.exists(processed_audio):
                    try:
                        os.remove(processed_audio)
                    except:
                        pass
        except Exception as e:
            print(f"[STT] ❌ Error transcribing audio: {e}")
            raise


# Global instance
_stt_service = None

def get_stt_service(model_name: str = None) -> STTService:
    """Get or create the global STT service instance"""
    global _stt_service
    if _stt_service is None:
        # Default to 'tiny' for faster processing, can be overridden with env var
        model = model_name or os.getenv("WHISPER_MODEL", "tiny")
        _stt_service = STTService(model_name=model)
    return _stt_service

