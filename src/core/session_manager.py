from typing import Dict, List
import json
import uuid
from datetime import datetime, timezone
from langchain_core.messages import HumanMessage, AIMessage
from src.core.storage_manager import StorageManager

class SessionManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.storage = StorageManager()
            self._initialized = True

    def create_session(self, session_id: str | None = None) -> str:
        """Create a new session and return the session_id"""
        session_id = session_id or str(uuid.uuid4())
        current_time = datetime.now(timezone.utc)
        
        if not self.storage.session_exists(session_id):
            self.storage.create_session(session_id, current_time, current_time)
        
        return session_id

    def get_session_timestamps(self, session_id: str) -> tuple[datetime, datetime]:
        """Get created_at and updated_at timestamps for a session"""
        current_time = datetime.now(timezone.utc)
        
        timestamps = self.storage.get_session_timestamps(session_id)
        if timestamps is None:
            # New session - set both created_at and updated_at
            self.storage.set_session_timestamps(session_id, current_time, current_time)
            return current_time, current_time
        else:
            # Existing session - update only updated_at, keep original created_at
            self.storage.update_session_timestamp(session_id, current_time)
            created_at = timestamps["created_at"]
            return created_at, current_time

    def get_chat_history(self, session_id: str) -> List:
        """Get chat history for a session"""
        return self.storage.get_chat_history(session_id)

    def update_chat_history(self, session_id: str, chat_history: List) -> None:
        """Update chat history for a session"""
        self.storage.update_chat_history(session_id, chat_history)

    def set_session_title(self, session_id: str, title: str) -> None:
        """Set the title for a session"""
        self.storage.set_session_title(session_id, title)

    def get_session_title(self, session_id: str) -> str:
        """Get the title for a session"""
        return self.storage.get_session_title(session_id)

    def clear_session(self, session_id: str) -> bool:
        """Clear a session and return True if it existed"""
        return self.storage.delete_session(session_id)

    def get_session_data(self, session_id: str) -> dict | None:
        """Get all data for a specific session"""
        if not self.storage.session_exists(session_id):
            return None
        
        # Get basic session info from storage
        metadata = self.storage.get_session_metadata(session_id)
        if metadata is None:
            return None
        
        # Get chat history
        chat_history = self.storage.get_chat_history(session_id)
        
        # Extract the latest response data from chat history
        latest_response = None
        latest_markdown = None
        latest_questions = []
        
        # Look for the latest AI message in chat history
        for message in reversed(chat_history):
            if hasattr(message, 'content') and isinstance(message.content, str):
                try:
                    # Try to parse the content as JSON (AI responses are stored as JSON)
                    parsed_content = json.loads(message.content)
                    if isinstance(parsed_content, dict):
                        latest_response = parsed_content.get("response", "")
                        latest_markdown = parsed_content.get("markdown", "")
                        latest_questions = parsed_content.get("questions", [])
                        break
                except (json.JSONDecodeError, AttributeError):
                    continue
        
        return {
            "session_id": session_id,
            "title": metadata["title"],
            "response": latest_response or "",
            "markdown": latest_markdown or "",
            "questions": latest_questions,
            "created_at": metadata["created_at"],
            "updated_at": metadata["updated_at"]
        }

    def get_session_with_conversation(self, session_id: str) -> dict | None:
        """Get session data including full conversation history"""
        return self.storage.get_all_session_data(session_id) 