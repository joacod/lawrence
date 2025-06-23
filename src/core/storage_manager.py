from typing import Dict, List, Optional
from datetime import datetime
import json

class StorageManager:
    """
    Storage manager responsible for all persistence operations.
    Currently uses in-memory storage, but designed to be easily replaced with database storage.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StorageManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            # In-memory storage (will be replaced with database in the future)
            self._sessions: Dict[str, List] = {}
            self._session_titles: Dict[str, str] = {}
            self._session_timestamps: Dict[str, Dict[str, datetime]] = {}
            self._initialized = True

    # Session operations
    def create_session(self, session_id: str, created_at: datetime, updated_at: datetime) -> None:
        """Create a new session in storage"""
        self._sessions[session_id] = []
        self._session_timestamps[session_id] = {
            "created_at": created_at,
            "updated_at": updated_at
        }

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists in storage"""
        return session_id in self._sessions

    def delete_session(self, session_id: str) -> bool:
        """Delete a session from storage"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            if session_id in self._session_titles:
                del self._session_titles[session_id]
            if session_id in self._session_timestamps:
                del self._session_timestamps[session_id]
            return True
        return False

    # Chat history operations
    def get_chat_history(self, session_id: str) -> List:
        """Get chat history for a session"""
        return self._sessions.get(session_id, [])

    def update_chat_history(self, session_id: str, chat_history: List) -> None:
        """Update chat history for a session"""
        self._sessions[session_id] = chat_history

    # Title operations
    def set_session_title(self, session_id: str, title: str) -> None:
        """Set the title for a session"""
        self._session_titles[session_id] = title

    def get_session_title(self, session_id: str) -> str:
        """Get the title for a session"""
        return self._session_titles.get(session_id, "Untitled Feature")

    # Timestamp operations
    def get_session_timestamps(self, session_id: str) -> Optional[Dict[str, datetime]]:
        """Get timestamps for a session"""
        return self._session_timestamps.get(session_id)

    def update_session_timestamp(self, session_id: str, updated_at: datetime) -> None:
        """Update the updated_at timestamp for a session"""
        if session_id in self._session_timestamps:
            self._session_timestamps[session_id]["updated_at"] = updated_at

    def set_session_timestamps(self, session_id: str, created_at: datetime, updated_at: datetime) -> None:
        """Set both created_at and updated_at timestamps for a session"""
        self._session_timestamps[session_id] = {
            "created_at": created_at,
            "updated_at": updated_at
        }

    # Data retrieval operations
    def get_session_metadata(self, session_id: str) -> Optional[Dict]:
        """Get session metadata (title and timestamps)"""
        if session_id not in self._sessions:
            return None
        
        timestamps = self._session_timestamps.get(session_id, {})
        return {
            "session_id": session_id,
            "title": self.get_session_title(session_id),
            "created_at": timestamps.get("created_at"),
            "updated_at": timestamps.get("updated_at")
        }

    def get_all_session_data(self, session_id: str) -> Optional[Dict]:
        """Get all conversation data for a session including full history"""
        if session_id not in self._sessions:
            return None
        
        # Get basic session info
        metadata = self.get_session_metadata(session_id)
        if metadata is None:
            return None
        
        # Get chat history
        chat_history = self._sessions[session_id]
        
        # Extract all conversation data from chat history
        conversation_data = []
        
        for i, message in enumerate(chat_history):
            if hasattr(message, 'content') and isinstance(message.content, str):
                # Check if this is a user message or AI response
                if hasattr(message, 'type') and message.type == "human":
                    # User message
                    conversation_data.append({
                        "type": "user",
                        "content": message.content,
                        "timestamp": metadata["updated_at"]  # We don't store individual timestamps yet
                    })
                else:
                    # AI response - try to parse JSON
                    try:
                        parsed_content = json.loads(message.content)
                        if isinstance(parsed_content, dict):
                            conversation_data.append({
                                "type": "assistant",
                                "response": parsed_content.get("response", ""),
                                "markdown": parsed_content.get("markdown", ""),
                                "questions": parsed_content.get("questions", []),
                                "timestamp": metadata["updated_at"]  # We don't store individual timestamps yet
                            })
                    except (json.JSONDecodeError, AttributeError):
                        # Fallback for non-JSON AI messages
                        conversation_data.append({
                            "type": "assistant",
                            "response": message.content,
                            "markdown": "",
                            "questions": [],
                            "timestamp": metadata["updated_at"]
                        })
        
        return {
            "session_id": session_id,
            "title": metadata["title"],
            "created_at": metadata["created_at"],
            "updated_at": metadata["updated_at"],
            "conversation": conversation_data
        } 