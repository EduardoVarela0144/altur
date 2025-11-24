"""
Call Transcription Service - Main Application
"""
import os
import sys
from flask import Flask
from flask_cors import CORS
from routes.calls_routes import calls_routes
from routes.auth_routes import auth_routes

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
CORS(app)  # Enable CORS for API access

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


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"[Main] ✅ Call Transcription Service starting")
    print(f"[Main] 📡 Server running on port {port}")
    try:
        app.run(debug=True, host='0.0.0.0', port=port)
    except KeyboardInterrupt:
        print("\n[Main] Stopping application...")
