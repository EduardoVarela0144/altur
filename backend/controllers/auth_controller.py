"""
Controller for authentication
"""
from flask import request, jsonify
from services.auth_service import get_auth_service


class AuthController:
    """Controller for authentication operations"""
    
    def __init__(self):
        self.auth_service = get_auth_service()
    
    def register(self):
        """Register a new user"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "success": False,
                    "error": "No data provided"
                }), 400
            
            username = data.get("username")
            password = data.get("password")
            email = data.get("email")
            
            if not username or not password:
                return jsonify({
                    "success": False,
                    "error": "Username and password are required"
                }), 400
            
            user_id = self.auth_service.create_user(username, password, email)
            if user_id:
                return jsonify({
                    "success": True,
                    "message": "User created successfully",
                    "user_id": user_id
                }), 201
            else:
                return jsonify({
                    "success": False,
                    "error": "Username already exists"
                }), 400
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    def login(self):
        """Login a user"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "success": False,
                    "error": "No data provided"
                }), 400
            
            username = data.get("username")
            password = data.get("password")
            
            if not username or not password:
                return jsonify({
                    "success": False,
                    "error": "Username and password are required"
                }), 400
            
            result = self.auth_service.authenticate(username, password)
            if result:
                return jsonify({
                    "success": True,
                    "data": result
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "error": "Invalid credentials"
                }), 401
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    def logout(self):
        """Logout a user"""
        try:
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            if not token:
                return jsonify({
                    "success": False,
                    "error": "Token required"
                }), 400
            
            success = self.auth_service.logout(token)
            if success:
                return jsonify({
                    "success": True,
                    "message": "Logged out successfully"
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "error": "Invalid token"
                }), 400
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


# Global instance
auth_controller = AuthController()

