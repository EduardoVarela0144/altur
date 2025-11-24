"""
Routes for call record management
"""
from flask import Blueprint, request, jsonify
from controllers.calls_controller import calls_controller
from flask_socketio import SocketIO, emit
import uuid

calls_routes = Blueprint('calls', __name__)

# This will be set from main.py
socketio = None
upload_service = None

def init_socketio(sio, upload_svc):
    """Initialize SocketIO and upload service"""
    global socketio, upload_service
    socketio = sio
    upload_service = upload_svc

# API Routes
@calls_routes.route('/api/calls', methods=['POST'])
def upload_call():
    """Upload and process an audio file"""
    # Check if WebSocket session ID is provided
    session_id = request.form.get('session_id') or request.headers.get('X-Session-ID')
    
    if session_id and socketio and upload_service:
        # Use WebSocket-based upload with progress
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "No file provided"
            }), 400
        
        file = request.files['file']
        if not file.filename:
            return jsonify({
                "success": False,
                "error": "No file selected"
            }), 400
        
        # Process in background with WebSocket updates
        upload_service.process_upload_async(file, session_id)
        
        return jsonify({
            "success": True,
            "message": "Upload started",
            "session_id": session_id
        }), 202
    else:
        # Fallback to original synchronous upload
        return calls_controller.upload_and_process()

@calls_routes.route('/api/calls', methods=['GET'])
def get_all_calls():
    """Get all call records with optional filtering by tag"""
    return calls_controller.get_all()

@calls_routes.route('/api/calls/analytics', methods=['GET'])
def get_analytics():
    """Get analytics about calls"""
    return calls_controller.get_analytics()

@calls_routes.route('/api/calls/<call_id>', methods=['GET'])
def get_call(call_id):
    """Get a single call record by ID"""
    return calls_controller.get_one(call_id)

@calls_routes.route('/api/calls/<call_id>/tags', methods=['PUT'])
def update_call_tags(call_id):
    """Update/override tags for a call record"""
    return calls_controller.update_tags(call_id)

@calls_routes.route('/api/calls/<call_id>/export', methods=['GET'])
def export_call(call_id):
    """Export a call record as JSON"""
    return calls_controller.export_call(call_id)

@calls_routes.route('/api/calls/<call_id>', methods=['DELETE'])
def delete_call(call_id):
    """Delete a call record"""
    return calls_controller.delete_one(call_id)

