from typing import Dict, List, Optional
from datetime import datetime
import json
import os

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
            self._session_questions: Dict[str, List[Dict]] = {}  # New: questions per session
            # Load initial sessions from mock file if present
            initial_sessions_path = os.path.join(os.path.dirname(__file__), 'storage_mock', 'initial_sessions.json')
            if os.path.exists(initial_sessions_path):
                with open(initial_sessions_path, 'r') as f:
                    try:
                        initial_sessions = json.load(f)
                        for session in initial_sessions:
                            session_id = session["session_id"]
                            self._sessions[session_id] = session.get("conversation", [])
                            self._session_titles[session_id] = session.get("title", "Untitled Feature")
                            # Parse timestamps as datetime objects
                            created_at = session.get("created_at")
                            updated_at = session.get("updated_at")
                            if created_at and updated_at:
                                self._session_timestamps[session_id] = {
                                    "created_at": datetime.fromisoformat(created_at.replace('Z', '+00:00')),
                                    "updated_at": datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                                }
                            # Extract questions from conversation if present
                            questions = []
                            for message in session.get("conversation", []):
                                chat = message.get("chat")
                                if chat and "questions" in chat:
                                    for q in chat["questions"]:
                                        questions.append(q)
                            if questions:
                                self._session_questions[session_id] = questions
                    except Exception as e:
                        print(f"Failed to load initial sessions: {e}")
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
            if session_id in self._session_questions:
                del self._session_questions[session_id]
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

    # Question operations
    def get_questions(self, session_id: str) -> List[Dict]:
        """Get all questions for a session"""
        return self._session_questions.get(session_id, [])

    def set_questions(self, session_id: str, questions: List[Dict]) -> None:
        """Set the questions list for a session"""
        self._session_questions[session_id] = questions

    def add_questions(self, session_id: str, new_questions: List[str]) -> None:
        """Add new questions to the session as pending if not already present"""
        existing = self._session_questions.get(session_id, [])
        existing_questions = {q['question'] for q in existing}
        for q in new_questions:
            if q not in existing_questions:
                existing.append({
                    'question': q,
                    'status': 'pending',
                    'user_answer': None
                })
        self._session_questions[session_id] = existing

    def answer_question(self, session_id: str, question: str, answer: str) -> None:
        """Mark a question as answered and store the user's answer"""
        questions = self._session_questions.get(session_id, [])
        for q in questions:
            if q['question'] == question:
                q['status'] = 'answered'
                q['user_answer'] = answer
        self._session_questions[session_id] = questions

    def disregard_question(self, session_id: str, question: str) -> None:
        """Mark a question as disregarded"""
        questions = self._session_questions.get(session_id, [])
        for q in questions:
            if q['question'] == question:
                q['status'] = 'disregarded'
                q['user_answer'] = None
        self._session_questions[session_id] = questions

    def get_pending_questions(self, session_id: str) -> List[Dict]:
        """Get all pending questions for a session"""
        return [q for q in self._session_questions.get(session_id, []) if q['status'] == 'pending']

    def get_answered_questions(self, session_id: str) -> List[Dict]:
        """Get all answered questions for a session"""
        return [q for q in self._session_questions.get(session_id, []) if q['status'] == 'answered']

    def get_disregarded_questions(self, session_id: str) -> List[Dict]:
        """Get all disregarded questions for a session"""
        return [q for q in self._session_questions.get(session_id, []) if q['status'] == 'disregarded']

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
        """Get all conversation data for a session including full history and questions"""
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
        
        # Add questions to the session data
        questions = self._session_questions.get(session_id, [])
        return {
            "session_id": session_id,
            "title": metadata["title"],
            "created_at": metadata["created_at"],
            "updated_at": metadata["updated_at"],
            "conversation": conversation_data,
            "questions": questions
        }

    def list_sessions(self) -> List[Dict[str, str]]:
        """Return a list of all sessions with session_id, title, and updated_at."""
        return [
            {
                "session_id": session_id,
                "title": self.get_session_title(session_id),
                "updated_at": self._session_timestamps.get(session_id, {}).get("updated_at")
            }
            for session_id in self._sessions.keys()
        ] 