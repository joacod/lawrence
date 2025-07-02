"""
Pure data persistence layer for session storage.
This will be replaced with database operations in the future.
Contains NO business logic - only CRUD operations.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os


class DataStore:
    """
    Pure data persistence layer responsible only for storing/retrieving data.
    No business logic, no data transformation, no filtering.
    Designed to be easily replaced with database implementation.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataStore, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            # Raw data storage - simple key-value store
            self._data: Dict[str, Dict[str, Any]] = {}
            self._load_initial_data()
            self._initialized = True
    
    def _load_initial_data(self) -> None:
        """Load initial mock data if present"""
        initial_sessions_path = os.path.join(os.path.dirname(__file__), 'storage_mock', 'initial_sessions.json')
        if os.path.exists(initial_sessions_path):
            try:
                with open(initial_sessions_path, 'r') as f:
                    initial_sessions = json.load(f)
                    for session in initial_sessions:
                        session_id = session["session_id"]
                        # Store raw session data without any transformation
                        self._data[session_id] = {
                            "conversation": session.get("conversation", []),
                            "title": session.get("title", "Untitled Feature"),
                            "created_at": session.get("created_at"),
                            "updated_at": session.get("updated_at"),
                            "questions": session.get("questions", [])
                        }
            except Exception as e:
                print(f"Failed to load initial sessions: {e}")
    
    # ========================================================================
    # PURE CRUD OPERATIONS - NO BUSINESS LOGIC
    # ========================================================================
    
    def store_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """Store session data - pure persistence operation"""
        self._data[session_id] = data.copy()
    
    def retrieve_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data - returns None if not found"""
        return self._data.get(session_id)
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session data - returns True if existed, False if not found"""
        if session_id in self._data:
            del self._data[session_id]
            return True
        return False
    
    def session_exists(self, session_id: str) -> bool:
        """Check if session exists in storage"""
        return session_id in self._data
    
    def list_session_ids(self) -> List[str]:
        """Get list of all session IDs"""
        return list(self._data.keys())
    
    def update_session_field(self, session_id: str, field: str, value: Any) -> bool:
        """Update a specific field in session data"""
        if session_id in self._data:
            self._data[session_id][field] = value
            return True
        return False
    
    def get_session_field(self, session_id: str, field: str, default: Any = None) -> Any:
        """Get a specific field from session data"""
        session_data = self._data.get(session_id, {})
        return session_data.get(field, default) 