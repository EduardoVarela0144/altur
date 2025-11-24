import os
import sys

# En Docker, usar 0.0.0.0 para escuchar en todas las interfaces
# En local, usar localhost
bind_host = os.getenv("BIND_HOST", "0.0.0.0")
bind_port = os.getenv("PORT", "5000")
bind = f"{bind_host}:{bind_port}"

workers = int(os.getenv("GUNICORN_WORKERS", "1"))  # SocketIO works better with 1 worker
timeout = int(os.getenv("GUNICORN_TIMEOUT", "1000"))
worker_class = "eventlet"  # Required for Flask-SocketIO
worker_connections = 1000
keepalive = 5

# Configuración de logging para mostrar todos los logs
loglevel = os.getenv("LOG_LEVEL", "info")
accesslog = "-"  # Logs de acceso a stdout
errorlog = "-"   # Logs de error a stderr
capture_output = True  # Capturar stdout/stderr de la aplicación
enable_stdio_inheritance = True  # Heredar stdout/stderr