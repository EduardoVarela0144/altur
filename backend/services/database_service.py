"""
Database Service for Call Transcription Service - MongoDB
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConfigurationError
from bson import ObjectId
from bson.errors import InvalidId


class DatabaseService:
    """Service for database operations with MongoDB"""
    
    def __init__(self, connection_string: Optional[str] = None, db_name: Optional[str] = None, lazy_init: bool = False):
        """
        Initialize MongoDB connection
        
        Args:
            connection_string: MongoDB connection string (defaults to MONGO_URI env var)
            db_name: Database name (defaults to MONGO_DB_NAME env var or 'call_transcription')
            lazy_init: If True, don't connect until needed
        """
        self.connection_string = connection_string or os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        self.db_name = db_name or os.getenv("MONGO_DB_NAME", "call_transcription")
        self._client = None
        self._db = None
        self._initialized = False
        
        if not lazy_init:
            self._ensure_connection()
    
    def _ensure_connection(self):
        """Ensure MongoDB connection is established"""
        if self._initialized and self._client is not None:
            return
        
        try:
            connection_options = {
                "serverSelectionTimeoutMS": 30000,
                "connectTimeoutMS": 30000,
                "socketTimeoutMS": 30000,
            }
            
            print(f"[Database] 🔌 Connecting to MongoDB...")
            self._client = MongoClient(self.connection_string, **connection_options)
            self._db = self._client[self.db_name]
            
            # Verify connection
            try:
                self._client.admin.command('ping')
            except Exception as ping_error:
                print(f"[Database] ⚠️ Error in initial ping: {ping_error}")
                raise
            
            self._initialized = True
            print(f"[Database] ✅ Connected to MongoDB: {self.db_name}")
            
            # Create indexes
            try:
                self._create_indexes()
            except Exception as index_error:
                print(f"[Database] ⚠️ Error creating indexes (non-critical): {index_error}")
            
        except (ServerSelectionTimeoutError, ConfigurationError) as e:
            error_msg = str(e)
            print(f"[Database] ⚠️ MongoDB connection error: {error_msg[:200]}")
            
            # Try alternative SSL configuration if needed
            if "SSL" in error_msg or "TLS" in error_msg or "tlsv1" in error_msg.lower():
                print(f"[Database] 🔄 SSL error detected, trying alternative configuration...")
                try:
                    connection_string_alt = self.connection_string
                    if "mongodb+srv://" in connection_string_alt and "?" not in connection_string_alt:
                        connection_string_alt = f"{connection_string_alt}?retryWrites=true&w=majority&tls=true"
                    
                    alt_options = {
                        "serverSelectionTimeoutMS": 30000,
                        "connectTimeoutMS": 30000,
                        "socketTimeoutMS": 30000,
                    }
                    
                    self._client = MongoClient(connection_string_alt, **alt_options)
                    self._db = self._client[self.db_name]
                    self._client.admin.command('ping')
                    
                    self._initialized = True
                    print(f"[Database] ✅ Connected to MongoDB with alternative configuration: {self.db_name}")
                    try:
                        self._create_indexes()
                    except Exception:
                        pass
                    return
                except Exception as alt_error:
                    print(f"[Database] ❌ Alternative configuration also failed: {str(alt_error)[:200]}")
            
            print(f"[Database] ⚠️ Verify:")
            print(f"   - Connection URL is correct (format: mongodb+srv://user:pass@cluster.mongodb.net/)")
            print(f"   - Credentials are valid")
            print(f"   - IP is in MongoDB Atlas whitelist (0.0.0.0/0 to allow all)")
            print(f"   - Cluster is active and not paused")
            print(f"   - User has read/write permissions")
            print(f"[Database] ⚠️ Connection will be retried when needed")
            self._initialized = False
        except Exception as e:
            print(f"[Database] ⚠️ Unexpected error connecting to MongoDB: {e}")
            import traceback
            traceback.print_exc()
            print(f"[Database] ⚠️ Connection will be retried when needed")
            self._initialized = False
    
    @property
    def client(self):
        """Getter for MongoDB client (lazy connection)"""
        self._ensure_connection()
        return self._client
    
    @property
    def db(self):
        """Getter for database (lazy connection)"""
        self._ensure_connection()
        return self._db
    
    @property
    def calls(self):
        """Getter for calls collection"""
        self._ensure_connection()
        return self._db.calls
    
    def _create_indexes(self):
        """Create necessary indexes in collections"""
        try:
            # Indexes for calls
            self.calls.create_index("upload_timestamp", background=True)
            self.calls.create_index("tags", background=True)
            self.calls.create_index([("upload_timestamp", -1)], background=True)
            
            # Indexes for users
            self.db.users.create_index("username", unique=True, background=True)
            
            # Indexes for tokens
            try:
                self.db.tokens.create_index("token", unique=True, background=True)
            except Exception:
                pass  # Index may already exist
            
            try:
                # Try to create TTL index, but handle if it already exists with different options
                existing_indexes = self.db.tokens.list_indexes()
                has_ttl = False
                for idx in existing_indexes:
                    if idx.get("name") == "expires_at_1" and idx.get("expireAfterSeconds") is not None:
                        has_ttl = True
                        break
                
                if not has_ttl:
                    # Drop existing index if it exists without TTL
                    try:
                        self.db.tokens.drop_index("expires_at_1")
                    except:
                        pass
                    # Create new index with TTL
                    self.db.tokens.create_index([("expires_at", 1)], expireAfterSeconds=0, background=True)
            except Exception as e:
                print(f"[Database] Note: TTL index setup skipped: {e}")
            
            print("[Database] ✅ Indexes created/verified")
        except Exception as e:
            print(f"[Database] ⚠️ Error creating indexes (may already exist): {e}")
    
    # ========== CALL RECORDS METHODS ==========
    
    def create_call_record(self, filename: str, audio_file_path: str, transcript: str = None, 
                          summary: str = None, tags: List[str] = None, roles: Dict = None,
                          emotions: List[str] = None, intent: str = None, mood: str = None,
                          insights: List[str] = None, tags_override: List[str] = None) -> str:
        """
        Create a new call record
        
        Args:
            filename: Audio file name
            audio_file_path: Path where file was saved
            transcript: Audio transcription (optional, can be None initially)
            summary: Call summary (optional)
            tags: List of tags (optional)
            roles: Dictionary of speaker roles (optional)
            emotions: List of detected emotions (optional)
            intent: Primary intent (optional)
            mood: Overall mood (optional)
            insights: List of insights (optional)
            tags_override: User-overridden tags (optional)
            
        Returns:
            str: ID of created record
        """
        try:
            # Use override tags if provided, otherwise use original tags
            final_tags = tags_override if tags_override is not None else (tags or [])
            
            call_doc = {
                "filename": filename,
                "audio_file_path": audio_file_path,
                "transcript": transcript or "",
                "summary": summary or "",
                "tags": final_tags,
                "tags_original": tags or [],
                "tags_override": tags_override,
                "roles": roles or {},
                "emotions": emotions or [],
                "intent": intent or "unknown",
                "mood": mood or "neutral",
                "insights": insights or [],
                "upload_timestamp": datetime.utcnow(),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            result = self.calls.insert_one(call_doc)
            return str(result.inserted_id)
        except Exception as e:
            print(f"[Database] Error creating call record: {e}")
            raise
    
    def update_call_record(self, call_id: str, transcript: str = None, summary: str = None, 
                          tags: List[str] = None, tags_override: List[str] = None,
                          roles: Dict = None, emotions: List[str] = None, intent: str = None,
                          mood: str = None, insights: List[str] = None) -> bool:
        """
        Update a call record with transcript, summary, tags, and analysis data
        
        Args:
            call_id: Record ID
            transcript: Audio transcription
            summary: Call summary
            tags: List of tags (original)
            tags_override: User-overridden tags
            roles: Dictionary of speaker roles
            emotions: List of detected emotions
            intent: Primary intent
            mood: Overall mood
            insights: List of insights
            
        Returns:
            bool: True if updated successfully
        """
        try:
            update_data = {"updated_at": datetime.utcnow()}
            
            if transcript is not None:
                update_data["transcript"] = transcript
            if summary is not None:
                update_data["summary"] = summary
            if tags is not None:
                update_data["tags_original"] = tags
            if tags_override is not None:
                update_data["tags_override"] = tags_override
                # Use override tags as the main tags
                update_data["tags"] = tags_override
            elif tags is not None:
                # If no override, use original tags
                update_data["tags"] = tags
            if roles is not None:
                update_data["roles"] = roles
            if emotions is not None:
                update_data["emotions"] = emotions
            if intent is not None:
                update_data["intent"] = intent
            if mood is not None:
                update_data["mood"] = mood
            if insights is not None:
                update_data["insights"] = insights
            
            if len(update_data) == 1:  # Only updated_at
                return False
            
            result = self.calls.update_one(
                {"_id": ObjectId(call_id)},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
        except (InvalidId, Exception) as e:
            print(f"[Database] Error updating call record: {e}")
            return False
    
    def get_call_by_id(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get a call record by ID"""
        try:
            doc = self.calls.find_one({"_id": ObjectId(call_id)})
            if doc:
                return {
                    "id": str(doc["_id"]),
                    "filename": doc.get("filename", ""),
                    "audio_file_path": doc.get("audio_file_path", ""),
                    "transcript": doc.get("transcript", ""),
                    "summary": doc.get("summary", ""),
                    "tags": doc.get("tags", []),
                    "tags_original": doc.get("tags_original", []),
                    "tags_override": doc.get("tags_override"),
                    "roles": doc.get("roles", {}),
                    "emotions": doc.get("emotions", []),
                    "intent": doc.get("intent", "unknown"),
                    "mood": doc.get("mood", "neutral"),
                    "insights": doc.get("insights", []),
                    "upload_timestamp": doc.get("upload_timestamp", "").isoformat() if isinstance(doc.get("upload_timestamp"), datetime) else str(doc.get("upload_timestamp", "")),
                    "created_at": doc.get("created_at", "").isoformat() if isinstance(doc.get("created_at"), datetime) else str(doc.get("created_at", "")),
                    "updated_at": doc.get("updated_at", "").isoformat() if isinstance(doc.get("updated_at"), datetime) else str(doc.get("updated_at", ""))
                }
            return None
        except (InvalidId, Exception):
            return None
    
    def get_all_calls(self, tag: Optional[str] = None, start_date: Optional[datetime] = None,
                     end_date: Optional[datetime] = None, limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Get all call records with optional filters
        
        Args:
            tag: Filter by tag (optional)
            start_date: Filter by start date (optional)
            end_date: Filter by end date (optional)
            limit: Result limit
            skip: Number of results to skip
            
        Returns:
            List of call records sorted by upload_timestamp (newest first)
        """
        query = {}
        if tag:
            query["tags"] = tag
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            if date_query:
                query["upload_timestamp"] = date_query
        
        cursor = self.calls.find(query).sort("upload_timestamp", -1).skip(skip).limit(limit)
        
        results = []
        for doc in cursor:
            results.append({
                "id": str(doc["_id"]),
                "filename": doc.get("filename", ""),
                "audio_file_path": doc.get("audio_file_path", ""),
                "transcript": doc.get("transcript", ""),
                "summary": doc.get("summary", ""),
                "tags": doc.get("tags", []),
                "tags_original": doc.get("tags_original", []),
                "tags_override": doc.get("tags_override"),
                "roles": doc.get("roles", {}),
                "emotions": doc.get("emotions", []),
                "intent": doc.get("intent", "unknown"),
                "mood": doc.get("mood", "neutral"),
                "insights": doc.get("insights", []),
                "upload_timestamp": doc.get("upload_timestamp", "").isoformat() if isinstance(doc.get("upload_timestamp"), datetime) else str(doc.get("upload_timestamp", "")),
                "created_at": doc.get("created_at", "").isoformat() if isinstance(doc.get("created_at"), datetime) else str(doc.get("created_at", "")),
                "updated_at": doc.get("updated_at", "").isoformat() if isinstance(doc.get("updated_at"), datetime) else str(doc.get("updated_at", ""))
            })
        
        return results
    
    def delete_call(self, call_id: str) -> bool:
        """Delete a call record"""
        try:
            result = self.calls.delete_one({"_id": ObjectId(call_id)})
            return result.deleted_count > 0
        except (InvalidId, Exception):
            return False


# Global instance for lazy initialization
_db_service = None

def _get_db_service():
    """Get the global database service instance (lazy initialization)"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService(lazy_init=True)
    return _db_service
