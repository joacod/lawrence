from src.core.session_manager import SessionManager

class SessionService:
    def __init__(self):
        self.session_manager = SessionManager()

    def clear_session(self, session_id: str) -> bool:
        """Clear a session"""
        return self.session_manager.clear_session(session_id)

    def get_session_with_conversation(self, session_id: str) -> dict | None:
        """Get session data with full conversation history"""
        return self.session_manager.get_session_with_conversation(session_id) 