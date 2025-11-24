"""
Authentication middleware
"""
from functools import wraps
from flask import request, jsonify
from services.auth_service import get_auth_service


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({
                "success": False,
                "error": "Authentication required"
            }), 401
        
        auth_service = get_auth_service()
        user = auth_service.validate_token(token)
        if not user:
            return jsonify({
                "success": False,
                "error": "Invalid or expired token"
            }), 401
        
        # Add user to request context
        request.current_user = user
        return f(*args, **kwargs)
    return decorated_function

