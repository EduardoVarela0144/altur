"""
Call Transcription Service - Main Application
"""
import os
import sys
from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
from routes.calls_routes import calls_routes, init_socketio
from routes.auth_routes import auth_routes
from services.upload_service import UploadService

# Configurar stdout/stderr para que se muestre en los logs de gunicorn
# Forzar que los prints se muestren inmediatamente (sin buffering)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
else:
    # Python < 3.7: usar unbuffered
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)  # 1 = line buffered
    sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 1)

# Inicializar Flask
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for API access

# Initialize SocketIO
# Use eventlet for async support with WebSockets
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='eventlet',
    logger=True,
    engineio_logger=True
)

# Initialize upload service
upload_service = UploadService(socketio)

# Initialize routes with SocketIO
init_socketio(socketio, upload_service)

# Register routes
app.register_blueprint(calls_routes)
app.register_blueprint(auth_routes)

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "call-transcription-service"}, 200

# Root endpoint
@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API information"""
    return {
        "service": "Call Transcription Service",
        "version": "1.0.0",
        "endpoints": {
            "upload": "POST /api/calls",
            "list": "GET /api/calls",
            "get": "GET /api/calls/<call_id>",
            "delete": "DELETE /api/calls/<call_id>"
        }
    }, 200


# SocketIO event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"[SocketIO] Client connected")
    emit('connected', {'message': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"[SocketIO] Client disconnected")

@socketio.on('join')
def handle_join(data):
    """Handle client joining a room"""
    session_id = data if isinstance(data, str) else (data.get('room', '') if isinstance(data, dict) else str(data))
    if session_id:
        join_room(session_id)
        print(f"[SocketIO] Client {request.sid} joined room {session_id}")
        emit('joined', {'room': session_id, 'message': f'Joined room {session_id}'})
    else:
        print(f"[SocketIO] Warning: join event received with invalid data: {data}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"[Main] ✅ Call Transcription Service starting")
    print(f"[Main] 📡 Server running on port {port}")
    print(f"[Main] 🔌 WebSocket server enabled")
    try:
        socketio.run(app, host='0.0.0.0', port=port, debug=True)
    except KeyboardInterrupt:
        print("\n[Main] Stopping application...")
