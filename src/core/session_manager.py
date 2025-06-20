from typing import Dict, List
import json
import uuid
from datetime import datetime, timezone
from langchain_core.messages import HumanMessage, AIMessage

class SessionManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.sessions: Dict[str, List] = {}
            self.session_titles: Dict[str, str] = {}
            self.session_timestamps: Dict[str, Dict[str, datetime]] = {}
            self._initialized = True

    def create_session(self, session_id: str | None = None) -> str:
        """Create a new session and return the session_id"""
        session_id = session_id or str(uuid.uuid4())
        if session_id not in self.sessions:
            self.sessions[session_id] = []
            self.session_timestamps[session_id] = {
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        return session_id

    def get_session_timestamps(self, session_id: str) -> tuple[datetime, datetime]:
        """Get created_at and updated_at timestamps for a session"""
        current_time = datetime.now(timezone.utc)
        
        if session_id not in self.session_timestamps:
            # New session - set both created_at and updated_at
            self.session_timestamps[session_id] = {
                "created_at": current_time,
                "updated_at": current_time
            }
            return current_time, current_time
        else:
            # Existing session - update only updated_at, keep original created_at
            self.session_timestamps[session_id]["updated_at"] = current_time
            created_at = self.session_timestamps[session_id]["created_at"]
            return created_at, current_time

    def get_chat_history(self, session_id: str) -> List:
        """Get chat history for a session"""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        return self.sessions[session_id]

    def update_chat_history(self, session_id: str, chat_history: List) -> None:
        """Update chat history for a session"""
        self.sessions[session_id] = chat_history

    def set_session_title(self, session_id: str, title: str) -> None:
        """Set the title for a session"""
        self.session_titles[session_id] = title

    def get_session_title(self, session_id: str) -> str:
        """Get the title for a session"""
        return self.session_titles.get(session_id, "Untitled Feature")

    def clear_session(self, session_id: str) -> bool:
        """Clear a session and return True if it existed"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            if session_id in self.session_titles:
                del self.session_titles[session_id]
            if session_id in self.session_timestamps:
                del self.session_timestamps[session_id]
            return True
        return False

    def get_session_data(self, session_id: str) -> dict | None:
        """Get all data for a specific session"""
        if session_id not in self.sessions:
            return None
        
        # Get basic session info
        title = self.get_session_title(session_id)
        timestamps = self.session_timestamps.get(session_id, {})
        created_at = timestamps.get("created_at")
        updated_at = timestamps.get("updated_at")
        
        # Get chat history
        chat_history = self.sessions[session_id]
        
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
            "title": title,
            "response": latest_response or "",
            "markdown": latest_markdown or "",
            "questions": latest_questions,
            "created_at": created_at,
            "updated_at": updated_at
        } 