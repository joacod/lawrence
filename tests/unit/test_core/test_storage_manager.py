import pytest
from datetime import datetime, timezone
from unittest.mock import patch

from src.core.storage_manager import StorageManager


class TestStorageManager:
    """Test the StorageManager class."""
    
    def setup_method(self):
        """Set up a fresh StorageManager instance for each test."""
        # Clear the singleton instance
        StorageManager._instance = None
        self.storage = StorageManager()
    
    def test_singleton_pattern(self):
        """Test that StorageManager follows singleton pattern."""
        storage1 = StorageManager()
        storage2 = StorageManager()
        
        assert storage1 is storage2
        assert id(storage1) == id(storage2)
    
    def test_create_session(self):
        """Test creating a new session."""
        session_id = "test-session-123"
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        self.storage.create_session(session_id, created_at, updated_at)
        
        assert self.storage.session_exists(session_id)
        assert session_id in self.storage._sessions
        assert session_id in self.storage._session_timestamps
    
    def test_session_exists(self):
        """Test checking if a session exists."""
        session_id = "test-session-123"
        
        # Session doesn't exist initially
        assert not self.storage.session_exists(session_id)
        
        # Create session
        self.storage.create_session(session_id, datetime.now(timezone.utc), datetime.now(timezone.utc))
        
        # Session should exist now
        assert self.storage.session_exists(session_id)
    
    def test_delete_session(self):
        """Test deleting a session."""
        session_id = "test-session-123"
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        # Create session
        self.storage.create_session(session_id, created_at, updated_at)
        self.storage.set_session_title(session_id, "Test Title")
        
        # Verify session exists
        assert self.storage.session_exists(session_id)
        
        # Delete session
        result = self.storage.delete_session(session_id)
        
        assert result is True
        assert not self.storage.session_exists(session_id)
        assert session_id not in self.storage._sessions
        assert session_id not in self.storage._session_titles
        assert session_id not in self.storage._session_timestamps
    
    def test_delete_nonexistent_session(self):
        """Test deleting a session that doesn't exist."""
        session_id = "nonexistent-session"
        
        result = self.storage.delete_session(session_id)
        
        assert result is False
    
    def test_get_chat_history(self):
        """Test getting chat history for a session."""
        session_id = "test-session-123"
        chat_history = ["message1", "message2", "message3"]
        
        # Create session and set chat history
        self.storage.create_session(session_id, datetime.now(timezone.utc), datetime.now(timezone.utc))
        self.storage.update_chat_history(session_id, chat_history)
        
        # Get chat history
        result = self.storage.get_chat_history(session_id)
        
        assert result == chat_history
    
    def test_get_chat_history_nonexistent_session(self):
        """Test getting chat history for a nonexistent session."""
        session_id = "nonexistent-session"
        
        result = self.storage.get_chat_history(session_id)
        
        assert result == []
    
    def test_update_chat_history(self):
        """Test updating chat history for a session."""
        session_id = "test-session-123"
        initial_history = ["message1"]
        updated_history = ["message1", "message2", "message3"]
        
        # Create session and set initial history
        self.storage.create_session(session_id, datetime.now(timezone.utc), datetime.now(timezone.utc))
        self.storage.update_chat_history(session_id, initial_history)
        
        # Verify initial history
        assert self.storage.get_chat_history(session_id) == initial_history
        
        # Update history
        self.storage.update_chat_history(session_id, updated_history)
        
        # Verify updated history
        assert self.storage.get_chat_history(session_id) == updated_history
    
    def test_set_and_get_session_title(self):
        """Test setting and getting session title."""
        session_id = "test-session-123"
        title = "User Login System"
        
        # Create session
        self.storage.create_session(session_id, datetime.now(timezone.utc), datetime.now(timezone.utc))
        
        # Set title
        self.storage.set_session_title(session_id, title)
        
        # Get title
        result = self.storage.get_session_title(session_id)
        
        assert result == title
    
    def test_get_session_title_nonexistent_session(self):
        """Test getting title for a nonexistent session."""
        session_id = "nonexistent-session"
        
        result = self.storage.get_session_title(session_id)
        
        assert result == "Untitled Feature"
    
    def test_get_session_timestamps(self):
        """Test getting session timestamps."""
        session_id = "test-session-123"
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        # Create session
        self.storage.create_session(session_id, created_at, updated_at)
        
        # Get timestamps
        result = self.storage.get_session_timestamps(session_id)
        
        assert result is not None
        assert result["created_at"] == created_at
        assert result["updated_at"] == updated_at
    
    def test_get_session_timestamps_nonexistent_session(self):
        """Test getting timestamps for a nonexistent session."""
        session_id = "nonexistent-session"
        
        result = self.storage.get_session_timestamps(session_id)
        
        assert result is None
    
    def test_update_session_timestamp(self):
        """Test updating session timestamp."""
        session_id = "test-session-123"
        created_at = datetime.now(timezone.utc)
        initial_updated_at = datetime.now(timezone.utc)
        new_updated_at = datetime.now(timezone.utc)
        
        # Create session
        self.storage.create_session(session_id, created_at, initial_updated_at)
        
        # Verify initial timestamp
        timestamps = self.storage.get_session_timestamps(session_id)
        assert timestamps["updated_at"] == initial_updated_at
        
        # Update timestamp
        self.storage.update_session_timestamp(session_id, new_updated_at)
        
        # Verify updated timestamp
        timestamps = self.storage.get_session_timestamps(session_id)
        assert timestamps["updated_at"] == new_updated_at
        assert timestamps["created_at"] == created_at  # Should remain unchanged
    
    def test_set_session_timestamps(self):
        """Test setting both created_at and updated_at timestamps."""
        session_id = "test-session-123"
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        # Set timestamps
        self.storage.set_session_timestamps(session_id, created_at, updated_at)
        
        # Verify timestamps
        timestamps = self.storage.get_session_timestamps(session_id)
        assert timestamps["created_at"] == created_at
        assert timestamps["updated_at"] == updated_at
    
    def test_get_session_metadata(self):
        """Test getting session metadata."""
        session_id = "test-session-123"
        title = "User Login System"
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        # Create session and set metadata
        self.storage.create_session(session_id, created_at, updated_at)
        self.storage.set_session_title(session_id, title)
        
        # Get metadata
        result = self.storage.get_session_metadata(session_id)
        
        assert result is not None
        assert result["session_id"] == session_id
        assert result["title"] == title
        assert result["created_at"] == created_at
        assert result["updated_at"] == updated_at
    
    def test_get_session_metadata_nonexistent_session(self):
        """Test getting metadata for a nonexistent session."""
        session_id = "nonexistent-session"
        
        result = self.storage.get_session_metadata(session_id)
        
        assert result is None
    
    def test_get_all_session_data(self):
        """Test getting all session data including conversation."""
        session_id = "test-session-123"
        title = "User Login System"
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        # Create session and set data
        self.storage.create_session(session_id, created_at, updated_at)
        self.storage.set_session_title(session_id, title)
        
        # Mock chat history with conversation messages
        chat_history = [
            type('MockMessage', (), {
                'content': 'Create a login system',
                'type': 'human'
            })(),
            type('MockMessage', (), {
                'content': '{"response": "I\'ll help you", "markdown": "# Feature", "questions": []}',
                'type': 'ai'
            })()
        ]
        self.storage.update_chat_history(session_id, chat_history)
        
        # Get all session data
        result = self.storage.get_all_session_data(session_id)
        
        assert result is not None
        assert result["session_id"] == session_id
        assert result["title"] == title
        assert result["created_at"] == created_at
        assert result["updated_at"] == updated_at
        assert "conversation" in result
        assert len(result["conversation"]) == 2
    
    def test_get_all_session_data_nonexistent_session(self):
        """Test getting all session data for a nonexistent session."""
        session_id = "nonexistent-session"
        
        result = self.storage.get_all_session_data(session_id)
        
        assert result is None
    
    def test_get_all_session_data_with_invalid_json(self):
        """Test getting session data when chat history contains invalid JSON."""
        session_id = "test-session-123"
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        # Create session
        self.storage.create_session(session_id, created_at, updated_at)
        
        # Mock chat history with invalid JSON
        chat_history = [
            type('MockMessage', (), {
                'content': 'Create a login system',
                'type': 'human'
            })(),
            type('MockMessage', (), {
                'content': 'invalid json content',
                'type': 'ai'
            })()
        ]
        self.storage.update_chat_history(session_id, chat_history)
        
        # Get all session data
        result = self.storage.get_all_session_data(session_id)
        
        assert result is not None
        assert "conversation" in result
        assert len(result["conversation"]) == 2
        
        # The invalid JSON message should be handled gracefully
        conversation = result["conversation"]
        assert conversation[0]["type"] == "user"
        assert conversation[1]["type"] == "assistant"
        assert conversation[1]["response"] == "invalid json content"
    
    def test_multiple_sessions_isolation(self):
        """Test that multiple sessions are isolated from each other."""
        session1_id = "session-1"
        session2_id = "session-2"
        
        # Create two sessions
        self.storage.create_session(session1_id, datetime.now(timezone.utc), datetime.now(timezone.utc))
        self.storage.create_session(session2_id, datetime.now(timezone.utc), datetime.now(timezone.utc))
        
        # Set different data for each session
        self.storage.set_session_title(session1_id, "Session 1 Title")
        self.storage.set_session_title(session2_id, "Session 2 Title")
        
        self.storage.update_chat_history(session1_id, ["message1"])
        self.storage.update_chat_history(session2_id, ["message2"])
        
        # Verify isolation
        assert self.storage.get_session_title(session1_id) == "Session 1 Title"
        assert self.storage.get_session_title(session2_id) == "Session 2 Title"
        
        assert self.storage.get_chat_history(session1_id) == ["message1"]
        assert self.storage.get_chat_history(session2_id) == ["message2"]
        
        # Delete one session
        self.storage.delete_session(session1_id)
        
        # Verify other session is unaffected
        assert not self.storage.session_exists(session1_id)
        assert self.storage.session_exists(session2_id)
        assert self.storage.get_session_title(session2_id) == "Session 2 Title" 