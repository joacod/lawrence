"""
Session Manager - Business Logic Layer for Session Management.
Handles all session-related operations and business rules.
Uses DataStore for pure persistence operations.
"""
from typing import List, Dict, Optional, Any
import json
import uuid
from datetime import datetime, timezone
from src.core.data_store import DataStore


class SessionManager:
    """
    Session Manager handles all session business logic and lifecycle.
    Contains NO persistence logic - delegates to DataStore.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.data_store = DataStore()
            self._initialized = True

    # ========================================================================
    # SESSION LIFECYCLE MANAGEMENT
    # ========================================================================

    def create_session(self, session_id: str | None = None) -> str:
        """Create a new session and return the session_id"""
        session_id = session_id or str(uuid.uuid4())
        current_time = datetime.now(timezone.utc)
        
        if not self.data_store.session_exists(session_id):
            # Initialize session with default structure
            session_data = {
                "conversation": [],
                "title": "Untitled Feature",
                "created_at": current_time.isoformat(),
                "updated_at": current_time.isoformat(),
                "questions": []
            }
            self.data_store.store_session(session_id, session_data)
        
        return session_id

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and return True if it existed"""
        return self.data_store.delete_session(session_id)
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a session and return True if it existed (alias for delete_session)"""
        return self.delete_session(session_id)

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists"""
        return self.data_store.session_exists(session_id)

    # ========================================================================
    # TIMESTAMP MANAGEMENT
    # ========================================================================

    def get_session_timestamps(self, session_id: str) -> tuple[datetime, datetime]:
        """Get created_at and updated_at timestamps for a session"""
        current_time = datetime.now(timezone.utc)
        
        session_data = self.data_store.retrieve_session(session_id)
        if session_data is None:
            # New session - create and return current time for both
            self.create_session(session_id)
            return current_time, current_time
        
        # Parse existing timestamps
        created_at_str = session_data.get("created_at")
        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00')) if created_at_str else current_time
        
        # Update the updated_at timestamp
        self.data_store.update_session_field(session_id, "updated_at", current_time.isoformat())
        
        return created_at, current_time

    # ========================================================================
    # CHAT HISTORY MANAGEMENT
    # ========================================================================

    def get_chat_history(self, session_id: str) -> List:
        """Get chat history for a session"""
        return self.data_store.get_session_field(session_id, "conversation", [])

    def update_chat_history(self, session_id: str, chat_history: List) -> None:
        """Update chat history for a session"""
        self.data_store.update_session_field(session_id, "conversation", chat_history)
        # Update timestamp
        self.data_store.update_session_field(session_id, "updated_at", datetime.now(timezone.utc).isoformat())

    # ========================================================================
    # TITLE MANAGEMENT
    # ========================================================================

    def set_session_title(self, session_id: str, title: str) -> None:
        """Set the title for a session"""
        self.data_store.update_session_field(session_id, "title", title)

    def get_session_title(self, session_id: str) -> str:
        """Get the title for a session"""
        return self.data_store.get_session_field(session_id, "title", "Untitled Feature")

    # ========================================================================
    # QUESTION MANAGEMENT - BUSINESS LOGIC
    # ========================================================================

    def get_questions(self, session_id: str) -> List[Dict]:
        """Get all questions for a session"""
        return self.data_store.get_session_field(session_id, "questions", [])

    def add_questions(self, session_id: str, new_questions: List[str], feature_type: str = "general", priority: str = "medium") -> None:
        """Add new questions to the session as pending if not already present"""
        existing_questions = self.get_questions(session_id)
        existing_question_texts = {q['question'] for q in existing_questions}
        
        # Add only new questions
        for question_text in new_questions:
            if question_text not in existing_question_texts:
                existing_questions.append({
                    'question': question_text,
                    'status': 'pending',
                    'user_answer': None,
                    'feature_type': feature_type,
                    'priority': priority
                })
        
        self.data_store.update_session_field(session_id, "questions", existing_questions)
    
    def add_questions_with_priorities(self, session_id: str, questions_with_priorities: List[Dict]) -> None:
        """Add questions with their calculated priorities."""
        existing_questions = self.get_questions(session_id)
        existing_question_texts = {q['question'] for q in existing_questions}
        
        # Add only new questions with their priorities
        for question_data in questions_with_priorities:
            question_text = question_data.get('question', '')
            if question_text and question_text not in existing_question_texts:
                existing_questions.append({
                    'question': question_text,
                    'status': 'pending',
                    'user_answer': None,
                    'feature_type': question_data.get('feature_type', 'general'),
                    'priority': question_data.get('priority', 'medium'),
                    'priority_score': question_data.get('priority_score', 0.0),
                    'priority_reasoning': question_data.get('priority_reasoning', '')
                })
        
        self.data_store.update_session_field(session_id, "questions", existing_questions)

    def set_questions(self, session_id: str, questions: List[Dict]) -> None:
        """Set the questions list for a session (replaces existing)"""
        self.data_store.update_session_field(session_id, "questions", questions)

    def answer_question(self, session_id: str, question: str, answer: str) -> None:
        """Mark a question as answered and store the user's answer"""
        questions = self.get_questions(session_id)
        for q in questions:
            if q['question'] == question:
                q['status'] = 'answered'
                q['user_answer'] = answer
                break
        self.data_store.update_session_field(session_id, "questions", questions)

    def disregard_question(self, session_id: str, question: str) -> None:
        """Mark a question as disregarded"""
        questions = self.get_questions(session_id)
        for q in questions:
            if q['question'] == question:
                q['status'] = 'disregarded'
                q['user_answer'] = None
                break
        self.data_store.update_session_field(session_id, "questions", questions)

    def get_pending_questions(self, session_id: str) -> List[Dict]:
        """Get all pending questions for a session"""
        questions = self.get_questions(session_id)
        return [q for q in questions if q['status'] == 'pending']

    def get_answered_questions(self, session_id: str) -> List[Dict]:
        """Get all answered questions for a session"""
        questions = self.get_questions(session_id)
        return [q for q in questions if q['status'] == 'answered']

    def get_disregarded_questions(self, session_id: str) -> List[Dict]:
        """Get all disregarded questions for a session"""
        questions = self.get_questions(session_id)
        return [q for q in questions if q['status'] == 'disregarded']

    def set_session_feature_type(self, session_id: str, feature_type: str) -> None:
        """Set the feature type for a session"""
        self.data_store.update_session_field(session_id, "feature_type", feature_type)

    def get_session_feature_type(self, session_id: str) -> str:
        """Get the feature type for a session"""
        return self.data_store.get_session_field(session_id, "feature_type", "general")

    def get_questions_by_feature_type(self, session_id: str, feature_type: str) -> List[Dict]:
        """Get all questions for a session filtered by feature type"""
        questions = self.get_questions(session_id)
        return [q for q in questions if q.get('feature_type', 'general') == feature_type]

    def get_questions_by_priority(self, session_id: str, priority: str) -> List[Dict]:
        """Get all questions for a session filtered by priority"""
        questions = self.get_questions(session_id)
        return [q for q in questions if q.get('priority', 'medium') == priority]
    
    def get_questions_ordered_by_priority(self, session_id: str) -> List[Dict]:
        """Get all questions for a session ordered by priority (critical -> high -> medium -> low)"""
        questions = self.get_questions(session_id)
        priority_order = ['critical', 'high', 'medium', 'low']
        
        def priority_key(question):
            priority = question.get('priority', 'medium')
            return priority_order.index(priority) if priority in priority_order else len(priority_order)
        
        return sorted(questions, key=priority_key)
    
    def get_priority_summary(self, session_id: str) -> Dict[str, int]:
        """Get a summary of question priorities for a session."""
        questions = self.get_questions(session_id)
        summary = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for question in questions:
            priority = question.get('priority', 'medium')
            if priority in summary:
                summary[priority] += 1
        
        return summary

    # ========================================================================
    # SESSION DATA AGGREGATION & TRANSFORMATION
    # ========================================================================

    def get_session_metadata(self, session_id: str) -> Optional[Dict]:
        """Get session metadata (title and timestamps)"""
        session_data = self.data_store.retrieve_session(session_id)
        if session_data is None:
            return None
        
        return {
            "session_id": session_id,
            "title": session_data.get("title", "Untitled Feature"),
            "created_at": session_data.get("created_at"),
            "updated_at": session_data.get("updated_at")
        }

    def get_session_with_conversation(self, session_id: str) -> Optional[Dict]:
        """Get complete session data with conversation history and questions"""
        session_data = self.data_store.retrieve_session(session_id)
        if session_data is None:
            return None
        
        # Parse timestamps
        created_at_str = session_data.get("created_at")
        updated_at_str = session_data.get("updated_at")
        
        created_at = None
        updated_at = None
        if created_at_str:
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        if updated_at_str:
            updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
        
        # Transform conversation data
        conversation_data = []
        chat_history = session_data.get("conversation", [])
        
        for i, message in enumerate(chat_history):
            # Handle both mock data (dict) and regular LangChain message objects
            if isinstance(message, dict):
                # Mock data format - message is already a dict
                conversation_data.append(message)
            elif hasattr(message, 'content') and isinstance(message.content, str):
                # Regular LangChain message format
                if hasattr(message, 'type') and message.type == "human":
                    # User message
                    conversation_data.append({
                        "type": "user",
                        "content": message.content,
                        "timestamp": updated_at
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
                                "timestamp": updated_at
                            })
                    except (json.JSONDecodeError, AttributeError):
                        # Fallback for non-JSON AI messages
                        conversation_data.append({
                            "type": "assistant",
                            "response": message.content,
                            "markdown": "",
                            "questions": [],
                            "timestamp": updated_at
                        })
        
        return {
            "session_id": session_id,
            "title": session_data.get("title", "Untitled Feature"),
            "created_at": created_at,
            "updated_at": updated_at,
            "conversation": conversation_data,
            "questions": session_data.get("questions", [])
        }

    def list_sessions(self) -> List[Dict[str, Any]]:
        """Return a list of all sessions with metadata"""
        session_list = []
        for session_id in self.data_store.list_session_ids():
            session_data = self.data_store.retrieve_session(session_id)
            if session_data:
                updated_at_str = session_data.get("updated_at")
                updated_at = None
                if updated_at_str:
                    try:
                        updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
                    except:
                        updated_at = None
                
                session_list.append({
                    "session_id": session_id,
                    "title": session_data.get("title", "Untitled Feature"),
                    "updated_at": updated_at
                })
        
        return session_list 