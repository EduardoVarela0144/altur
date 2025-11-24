"""
Service for handling file uploads with progress updates via WebSocket
"""
import os
import uuid
import threading
import time
from werkzeug.utils import secure_filename
from services.database_service import DatabaseService
from services.stt_service import get_stt_service
from services.llm_service import get_llm_service
from flask_socketio import SocketIO


class UploadService:
    """Service for processing uploads with progress updates"""
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.db_service = DatabaseService()
        self.stt_service = get_stt_service()
        self.llm_service = get_llm_service()
        self.upload_folder = os.getenv("UPLOAD_FOLDER", "uploads")
        os.makedirs(self.upload_folder, exist_ok=True)
        self.allowed_extensions = {'.wav', '.mp3', '.m4a', '.ogg', '.flac', '.webm'}
    
    def _send_progress(self, session_id: str, stage: str, progress: int, message: str = ""):
        """Send progress update via WebSocket"""
        # Emit to room (clients join the room with session_id)
        # Also emit to all clients as fallback (in case room join failed)
        data = {
            'session_id': session_id,
            'stage': stage,
            'progress': progress,
            'message': message
        }
        # Try room first
        self.socketio.emit('upload_progress', data, room=session_id)
        # Also broadcast to all as fallback (client will filter by session_id)
        self.socketio.emit('upload_progress', data)
        print(f"[Upload] {stage}: {progress}% - {message} (room: {session_id})")
    
    def process_upload_async(self, file, session_id: str):
        """Process upload in background thread with progress updates"""
        call_id = None
        file_path = None
        
        try:
            # Stage 1: Validate and save file (0-20%)
            self._send_progress(session_id, 'uploading', 0, 'Validating file...')
            
            if not file.filename or file.filename == '':
                self._send_progress(session_id, 'error', 0, 'No file selected')
                return
            
            if not any(file.filename.lower().endswith(ext) for ext in self.allowed_extensions):
                self._send_progress(session_id, 'error', 0, 'Invalid file type')
                return
            
            # Check file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            max_size = 100 * 1024 * 1024  # 100MB
            if file_size > max_size:
                self._send_progress(session_id, 'error', 0, f'File too large (max 100MB)')
                return
            
            if file_size == 0:
                self._send_progress(session_id, 'error', 0, 'File is empty')
                return
            
            self._send_progress(session_id, 'uploading', 10, 'Saving file...')
            
            # Generate unique filename
            original_filename = secure_filename(file.filename)
            if not original_filename:
                self._send_progress(session_id, 'error', 0, 'Invalid filename')
                return
            
            file_ext = os.path.splitext(original_filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = os.path.join(self.upload_folder, unique_filename)
            
            # Save file
            file.save(file_path)
            self._send_progress(session_id, 'uploading', 20, 'File saved')
            
            # Stage 2: Create database record (20-25%)
            self._send_progress(session_id, 'processing', 25, 'Creating call record...')
            call_id = self.db_service.create_call_record(
                filename=original_filename,
                audio_file_path=file_path
            )
            self._send_progress(session_id, 'processing', 30, 'Call record created')
            
            # Stage 3: Transcribe audio (30-70%)
            self._send_progress(session_id, 'transcribing', 30, 'Starting transcription...')
            
            # Process transcription in thread to avoid blocking
            def transcription_progress():
                try:
                    # Send progress update before starting
                    self._send_progress(session_id, 'transcribing', 35, 'Processing audio...')
                    
                    # Transcribe with timeout protection
                    transcript = None
                    transcription_error = None
                    
                    def do_transcribe():
                        nonlocal transcript, transcription_error
                        try:
                            transcript = self.stt_service.transcribe(file_path)
                        except Exception as e:
                            transcription_error = e
                    
                    # Run transcription in a thread with timeout
                    transcribe_thread = threading.Thread(target=do_transcribe)
                    transcribe_thread.daemon = True
                    transcribe_thread.start()
                    
                    # Send periodic progress updates during transcription
                    start_time = time.time()
                    timeout_seconds = 300  # 5 minutes
                    last_progress_update = 0
                    while transcribe_thread.is_alive():
                        elapsed = time.time() - start_time
                        if elapsed > timeout_seconds:
                            raise TimeoutError("Transcription timed out after 5 minutes")
                        
                        # Send progress update every 2 seconds for better feedback
                        elapsed_int = int(elapsed)
                        if elapsed_int != last_progress_update and elapsed_int % 2 == 0:
                            last_progress_update = elapsed_int
                            # Calculate progress: 35% to 70% based on elapsed time
                            # Assume average transcription takes 60 seconds, scale accordingly
                            estimated_duration = 60  # Average transcription time in seconds
                            if elapsed < estimated_duration:
                                progress_pct = min(35 + int((elapsed / estimated_duration) * 35), 70)
                            else:
                                # If taking longer, gradually increase to 70%
                                progress_pct = min(35 + int((elapsed / timeout_seconds) * 35), 70)
                            
                            self._send_progress(
                                session_id, 
                                'transcribing', 
                                progress_pct, 
                                f'Transcribing audio... ({elapsed_int}s)'
                            )
                        time.sleep(0.5)  # Check every 0.5 seconds
                    
                    transcribe_thread.join(timeout=1)  # Final join
                    
                    if transcription_error:
                        raise transcription_error
                    
                    if not transcript or not transcript.strip():
                        transcript = "[Empty transcript - audio may be silent or unclear]"
                    
                    self._send_progress(session_id, 'transcribing', 70, 'Transcription complete')
                except Exception as e:
                    print(f"[Upload] Transcription error: {e}")
                    self._send_progress(session_id, 'error', 0, f'Transcription failed: {str(e)}')
                    raise
                
                # Stage 4: Analyze with LLM (70-90%)
                self._send_progress(session_id, 'analyzing', 70, 'Analyzing transcript...')
                
                try:
                    # Truncate transcript if too long to speed up LLM processing
                    max_transcript_length = 1000  # Further reduced to 1000 chars for faster processing
                    if len(transcript) > max_transcript_length:
                        transcript_for_analysis = transcript[:max_transcript_length] + "... [truncated]"
                        print(f"[Upload] Transcript truncated from {len(transcript)} to {len(transcript_for_analysis)} chars for faster analysis")
                    else:
                        transcript_for_analysis = transcript
                    
                    # Analyze with timeout protection and progress updates
                    analysis = None
                    analysis_error = None
                    analysis_start_time = time.time()
                    
                    def do_analyze():
                        nonlocal analysis, analysis_error
                        try:
                            analysis = self.llm_service.analyze_transcript(transcript_for_analysis)
                        except Exception as e:
                            analysis_error = e
                    
                    analyze_thread = threading.Thread(target=do_analyze)
                    analyze_thread.daemon = True
                    analyze_thread.start()
                    
                    # Send progress updates during LLM analysis
                    timeout_llm = 60  # 1 minute timeout
                    last_llm_update = 0
                    while analyze_thread.is_alive():
                        elapsed_llm = time.time() - analysis_start_time
                        if elapsed_llm > timeout_llm:
                            raise TimeoutError("LLM analysis timed out after 1 minute")
                        
                        # Update progress every 2 seconds during LLM analysis
                        elapsed_int = int(elapsed_llm)
                        if elapsed_int != last_llm_update and elapsed_int % 2 == 0:
                            last_llm_update = elapsed_int
                            # Progress from 70% to 90% during LLM analysis
                            progress_pct = min(70 + int((elapsed_llm / timeout_llm) * 20), 90)
                            self._send_progress(
                                session_id,
                                'analyzing',
                                progress_pct,
                                f'Analyzing transcript... ({elapsed_int}s)'
                            )
                        time.sleep(0.5)
                    
                    analyze_thread.join(timeout=1)
                    
                    if analyze_thread.is_alive():
                        raise TimeoutError("LLM analysis timed out after 1 minute")
                    
                    if analysis_error:
                        raise analysis_error
                    
                    if not analysis:
                        raise ValueError("No analysis result from LLM")
                    
                    if not analysis or not isinstance(analysis, dict):
                        raise ValueError("Invalid analysis result from LLM")
                    
                    summary = analysis.get("summary", "Unable to generate summary.")
                    tags = analysis.get("tags", [])
                    roles = analysis.get("roles", {})
                    emotions = analysis.get("emotions", [])
                    intent = analysis.get("intent", "unknown")
                    mood = analysis.get("mood", "neutral")
                    insights = analysis.get("insights", [])
                    
                    if not isinstance(tags, list):
                        tags = [tags] if tags else []
                    if not isinstance(emotions, list):
                        emotions = [emotions] if emotions else []
                    if not isinstance(insights, list):
                        insights = [insights] if insights else []
                    if not isinstance(roles, dict):
                        roles = {}
                    
                except Exception as llm_error:
                    print(f"[Upload] LLM analysis failed: {llm_error}")
                    summary = "Analysis failed - transcript available but summary could not be generated."
                    tags = ["analysis-error"]
                    roles = {}
                    emotions = []
                    intent = "unknown"
                    mood = "neutral"
                    insights = []
                
                self._send_progress(session_id, 'analyzing', 90, 'Analysis complete')
                
                # Stage 5: Update database (90-100%)
                self._send_progress(session_id, 'saving', 90, 'Saving results...')
                
                self.db_service.update_call_record(
                    call_id=call_id,
                    transcript=transcript,
                    summary=summary,
                    tags=tags,
                    roles=roles,
                    emotions=emotions,
                    intent=intent,
                    mood=mood,
                    insights=insights
                )
                
                # Get final record
                call_record = self.db_service.get_call_by_id(call_id)
                
                self._send_progress(session_id, 'complete', 100, 'Processing complete!')
                
                # Send final result
                complete_data = {
                    'session_id': session_id,
                    'success': True,
                    'data': call_record
                }
                # Try room first
                self.socketio.emit('upload_complete', complete_data, room=session_id)
                # Also broadcast to all as fallback
                self.socketio.emit('upload_complete', complete_data)
                print(f"[Upload] Sent upload_complete to room {session_id}")
            
            # Run transcription in thread to allow progress updates
            thread = threading.Thread(target=transcription_progress)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            print(f"[Upload] Error processing upload: {e}")
            import traceback
            traceback.print_exc()
            
            self._send_progress(session_id, 'error', 0, f'Error: {str(e)}')
            
            # Cleanup on error
            if call_id:
                try:
                    self.db_service.delete_call(call_id)
                except:
                    pass
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            
            error_data = {
                'session_id': session_id,
                'success': False,
                'error': str(e)
            }
            # Try room first
            self.socketio.emit('upload_complete', error_data, room=session_id)
            # Also broadcast to all as fallback
            self.socketio.emit('upload_complete', error_data)
            print(f"[Upload] Sent upload_complete (error) to room {session_id}")

