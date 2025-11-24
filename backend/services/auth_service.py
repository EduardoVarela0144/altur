"""
Basic Authentication Service
"""
import os
import hashlib
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
from services.database_service import DatabaseService


class AuthService:
    """Service for basic authentication"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(32))
        self.token_expiry_hours = int(os.getenv("TOKEN_EXPIRY_HOURS", "24"))
    
    @property
    def users(self):
        """Getter for users collection"""
        self.db_service._ensure_connection()
        return self.db_service.db.users
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_token(self) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(32)
    
    def create_user(self, username: str, password: str, email: str = None) -> Optional[str]:
        """
        Create a new user
        
        Args:
            username: Username
            password: Plain text password
            email: Email address (optional)
            
        Returns:
            User ID if successful, None otherwise
        """
        try:
            # Check if user exists
            existing = self.users.find_one({"username": username})
            if existing:
                return None
            
            hashed_password = self._hash_password(password)
            user_doc = {
                "username": username,
                "password": hashed_password,
                "email": email,
                "created_at": datetime.utcnow(),
                "active": True
            }
            result = self.users.insert_one(user_doc)
            return str(result.inserted_id)
        except Exception as e:
            print(f"[Auth] Error creating user: {e}")
            return None
    
    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            User dict if authenticated, None otherwise
        """
        try:
            # Try to find user by username first, then by email
            user = self.users.find_one({
                "$or": [
                    {"username": username, "active": True},
                    {"email": username, "active": True}
                ]
            })
            if not user:
                print(f"[Auth] User not found (username or email): {username}")
                return None
            
            hashed_password = self._hash_password(password)
            stored_password = user.get("password", "")
            
            print(f"[Auth] Debug - Username: {username}")
            print(f"[Auth] Debug - Stored password hash: {stored_password[:20]}...")
            print(f"[Auth] Debug - Provided password hash: {hashed_password[:20]}...")
            print(f"[Auth] Debug - Passwords match: {stored_password == hashed_password}")
            
            if stored_password != hashed_password:
                print(f"[Auth] Password mismatch for user: {username}")
                return None
            
            # Generate token
            token = self._generate_token()
            expires_at = datetime.utcnow() + timedelta(hours=self.token_expiry_hours)
            
            # Store token
            self.db_service.db.tokens.insert_one({
                "user_id": str(user["_id"]),
                "token": token,
                "expires_at": expires_at,
                "created_at": datetime.utcnow()
            })
            
            return {
                "user_id": str(user["_id"]),
                "username": user["username"],
                "email": user.get("email"),
                "token": token,
                "expires_at": expires_at.isoformat()
            }
        except Exception as e:
            print(f"[Auth] Error authenticating: {e}")
            return None
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a token
        
        Args:
            token: Authentication token
            
        Returns:
            User dict if token is valid, None otherwise
        """
        try:
            token_doc = self.db_service.db.tokens.find_one({
                "token": token,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if not token_doc:
                return None
            
            # Convert user_id string to ObjectId
            try:
                user_id = ObjectId(token_doc["user_id"])
            except Exception as e:
                print(f"[Auth] Error converting user_id to ObjectId: {e}")
                return None
            
            user = self.users.find_one({"_id": user_id, "active": True})
            if not user:
                return None
            
            return {
                "user_id": str(user["_id"]),
                "username": user["username"],
                "email": user.get("email")
            }
        except Exception as e:
            print(f"[Auth] Error validating token: {e}")
            return None
    
    def logout(self, token: str) -> bool:
        """Invalidate a token"""
        try:
            result = self.db_service.db.tokens.delete_one({"token": token})
            return result.deleted_count > 0
        except Exception as e:
            print(f"[Auth] Error logging out: {e}")
            return False


# Global instance
_auth_service = None

def get_auth_service() -> AuthService:
    """Get or create the global auth service instance"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service

