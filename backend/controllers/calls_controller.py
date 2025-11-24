"""
Controller for processing and managing call records
"""
import os
import uuid
from flask import request, jsonify
from werkzeug.utils import secure_filename
from services.database_service import DatabaseService
from services.stt_service import get_stt_service
from services.llm_service import get_llm_service


class CallsController:
    """Controller for call record operations"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.stt_service = get_stt_service()
        self.llm_service = get_llm_service()
        self.upload_folder = os.getenv("UPLOAD_FOLDER", "uploads")
        
        # Create upload folder if it doesn't exist
        os.makedirs(self.upload_folder, exist_ok=True)
        
        # Allowed audio file extensions
        self.allowed_extensions = {'.wav', '.mp3', '.m4a', '.ogg', '.flac', '.webm'}
    
    def _allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return any(filename.lower().endswith(ext) for ext in self.allowed_extensions)
    
    def upload_and_process(self):
        """Handle file upload and process it (transcribe + analyze)"""
        # Validate file presence
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "No file provided. Please include a 'file' field in the request."
            }), 400
        
        file = request.files['file']
        
        # Validate filename
        if not file.filename or file.filename == '':
            return jsonify({
                "success": False,
                "error": "No file selected or empty filename"
            }), 400
        
        # Validate file type
        if not self._allowed_file(file.filename):
            return jsonify({
                "success": False,
                "error": f"Invalid file type. Allowed types: {', '.join(sorted(self.allowed_extensions))}"
            }), 400
        
        # Validate file size (max 100MB)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        max_size = 100 * 1024 * 1024  # 100MB
        if file_size > max_size:
            return jsonify({
                "success": False,
                "error": f"File too large. Maximum size is 100MB, got {file_size / (1024*1024):.2f}MB"
            }), 400
        
        if file_size == 0:
            return jsonify({
                "success": False,
                "error": "File is empty"
            }), 400
        
        call_id = None
        file_path = None
        
        try:
            # Generate unique filename
            original_filename = secure_filename(file.filename)
            if not original_filename:
                return jsonify({
                    "success": False,
                    "error": "Invalid filename"
                }), 400
            
            file_ext = os.path.splitext(original_filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = os.path.join(self.upload_folder, unique_filename)
            
            # Save file
            try:
                file.save(file_path)
                print(f"[Calls] File saved: {file_path}")
            except Exception as save_error:
                return jsonify({
                    "success": False,
                    "error": f"Failed to save file: {str(save_error)}"
                }), 500
            
            # Verify file was saved
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                return jsonify({
                    "success": False,
                    "error": "File was not saved correctly"
                }), 500
            
            # Create initial call record
            try:
                call_id = self.db_service.create_call_record(
                    filename=original_filename,
                    audio_file_path=file_path
                )
            except Exception as db_error:
                # Clean up file if DB insert fails
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass
                return jsonify({
                    "success": False,
                    "error": f"Failed to create call record: {str(db_error)}"
                }), 500
            
            # Process transcription and analysis
            try:
                # Transcribe
                transcript = self.stt_service.transcribe(file_path)
                
                # Validate transcript
                if not transcript or not transcript.strip():
                    transcript = "[Empty transcript - audio may be silent or unclear]"
                    print(f"[Calls] ⚠️ Empty transcript for call {call_id}")
                
                # Analyze with LLM
                try:
                    analysis = self.llm_service.analyze_transcript(transcript)
                    
                    # Validate analysis result
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
                    print(f"[Calls] ⚠️ LLM analysis failed: {llm_error}")
                    # Use fallback values
                    summary = "Analysis failed - transcript available but summary could not be generated."
                    tags = ["analysis-error"]
                    roles = {}
                    emotions = []
                    intent = "unknown"
                    mood = "neutral"
                    insights = []
                
                # Update call record
                update_success = self.db_service.update_call_record(
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
                
                if not update_success:
                    print(f"[Calls] ⚠️ Failed to update call record {call_id} with transcript/summary/tags")
                
                # Get updated record
                call_record = self.db_service.get_call_by_id(call_id)
                if not call_record:
                    return jsonify({
                        "success": False,
                        "error": "Call record created but could not be retrieved"
                    }), 500
                
                return jsonify({
                    "success": True,
                    "data": call_record,
                    "message": "Call processed successfully"
                }), 201
                
            except FileNotFoundError as file_error:
                return jsonify({
                    "success": False,
                    "error": f"Audio file not found: {str(file_error)}",
                    "call_id": call_id
                }), 500
            except Exception as process_error:
                print(f"[Calls] ❌ Error processing call: {process_error}")
                import traceback
                traceback.print_exc()
                
                # Return partial record (without transcript/summary/tags)
                call_record = self.db_service.get_call_by_id(call_id) if call_id else None
                return jsonify({
                    "success": False,
                    "error": f"File uploaded but processing failed: {str(process_error)}",
                    "data": call_record,
                    "call_id": call_id
                }), 500
        
        except ValueError as val_error:
            return jsonify({
                "success": False,
                "error": f"Invalid input: {str(val_error)}"
            }), 400
        except Exception as e:
            print(f"[Calls] ❌ Unexpected error uploading file: {e}")
            import traceback
            traceback.print_exc()
            
            # Cleanup on unexpected error
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
            
            return jsonify({
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }), 500
    
    def get_all(self):
        """Get all call records with optional filtering and sorting"""
        try:
            from datetime import datetime
            
            tag = request.args.get('tag', None)
            start_date_str = request.args.get('start_date', None)
            end_date_str = request.args.get('end_date', None)
            
            # Parse date filters
            start_date = None
            end_date = None
            if start_date_str:
                try:
                    start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                except:
                    pass
            if end_date_str:
                try:
                    end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                except:
                    pass
            
            # Validate and parse limit
            try:
                limit = int(request.args.get('limit', 100))
                if limit < 1 or limit > 1000:
                    limit = 100
            except (ValueError, TypeError):
                limit = 100
            
            # Validate and parse skip
            try:
                skip = int(request.args.get('skip', 0))
                if skip < 0:
                    skip = 0
            except (ValueError, TypeError):
                skip = 0
            
            calls = self.db_service.get_all_calls(
                tag=tag,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                skip=skip
            )
            
            return jsonify({
                "success": True,
                "data": calls,
                "count": len(calls),
                "limit": limit,
                "skip": skip
            }), 200
        except Exception as e:
            print(f"[Calls] ❌ Error getting calls: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": f"Failed to retrieve calls: {str(e)}"
            }), 500
    
    def get_one(self, call_id: str):
        """Get a single call record by ID"""
        if not call_id or not call_id.strip():
            return jsonify({
                "success": False,
                "error": "Invalid call ID"
            }), 400
        
        try:
            call = self.db_service.get_call_by_id(call_id)
            if call:
                return jsonify({
                    "success": True,
                    "data": call
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "error": f"Call record not found with ID: {call_id}"
                }), 404
        except ValueError as val_error:
            return jsonify({
                "success": False,
                "error": f"Invalid call ID format: {str(val_error)}"
            }), 400
        except Exception as e:
            print(f"[Calls] ❌ Error getting call {call_id}: {e}")
            return jsonify({
                "success": False,
                "error": f"Failed to retrieve call: {str(e)}"
            }), 500
    
    def export_call(self, call_id: str):
        """Export a call record as JSON"""
        if not call_id or not call_id.strip():
            return jsonify({
                "success": False,
                "error": "Invalid call ID"
            }), 400
        
        try:
            call = self.db_service.get_call_by_id(call_id)
            if not call:
                return jsonify({
                    "success": False,
                    "error": f"Call record not found with ID: {call_id}"
                }), 404
            
            # Return as downloadable JSON
            from flask import Response
            import json
            json_data = json.dumps(call, indent=2, ensure_ascii=False)
            return Response(
                json_data,
                mimetype='application/json',
                headers={
                    'Content-Disposition': f'attachment; filename=call_{call_id}.json'
                }
            )
        except Exception as e:
            print(f"[Calls] ❌ Error exporting call {call_id}: {e}")
            return jsonify({
                "success": False,
                "error": f"Failed to export call: {str(e)}"
            }), 500
    
    def get_analytics(self):
        """Get analytics about calls"""
        try:
            all_calls = self.db_service.get_all_calls(limit=10000)
            
            total_calls = len(all_calls)
            total_tags = sum(len(call.get("tags", [])) for call in all_calls)
            avg_tags = total_tags / total_calls if total_calls > 0 else 0
            
            # Tag distribution
            tag_counts = {}
            for call in all_calls:
                for tag in call.get("tags", []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            # Calls with/without transcript
            calls_with_transcript = sum(1 for call in all_calls if call.get("transcript", "").strip())
            calls_without_transcript = total_calls - calls_with_transcript
            
            return jsonify({
                "success": True,
                "data": {
                    "total_calls": total_calls,
                    "total_tags": total_tags,
                    "average_tags_per_call": round(avg_tags, 2),
                    "calls_with_transcript": calls_with_transcript,
                    "calls_without_transcript": calls_without_transcript,
                    "tag_distribution": dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True))
                }
            }), 200
        except Exception as e:
            print(f"[Calls] ❌ Error getting analytics: {e}")
            return jsonify({
                "success": False,
                "error": f"Failed to retrieve analytics: {str(e)}"
            }), 500
    
    def update_tags(self, call_id: str):
        """Update/override tags for a call record"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "success": False,
                    "error": "No data provided"
                }), 400
            
            tags_override = data.get("tags")
            if tags_override is None:
                return jsonify({
                    "success": False,
                    "error": "Tags field is required"
                }), 400
            
            if not isinstance(tags_override, list):
                return jsonify({
                    "success": False,
                    "error": "Tags must be a list"
                }), 400
            
            # Verify call exists
            call = self.db_service.get_call_by_id(call_id)
            if not call:
                return jsonify({
                    "success": False,
                    "error": "Call record not found"
                }), 404
            
            # Update tags with override
            success = self.db_service.update_call_record(
                call_id=call_id,
                tags_override=tags_override
            )
            
            if success:
                updated_call = self.db_service.get_call_by_id(call_id)
                return jsonify({
                    "success": True,
                    "data": updated_call,
                    "message": "Tags updated successfully"
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "error": "Failed to update tags"
                }), 500
        except Exception as e:
            print(f"[Calls] ❌ Error updating tags: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    def delete_one(self, call_id: str):
        """Delete a call record"""
        try:
            # Get call record to delete audio file
            call = self.db_service.get_call_by_id(call_id)
            if not call:
                return jsonify({
                    "success": False,
                    "error": "Call record not found"
                }), 404
            
            # Delete audio file if it exists
            audio_path = call.get("audio_file_path")
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                    print(f"[Calls] Deleted audio file: {audio_path}")
                except Exception as e:
                    print(f"[Calls] ⚠️ Error deleting audio file: {e}")
            
            # Delete database record
            success = self.db_service.delete_call(call_id)
            if success:
                return jsonify({
                    "success": True,
                    "message": "Call record deleted"
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "error": "Failed to delete call record"
                }), 500
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


# Global instance
calls_controller = CallsController()

