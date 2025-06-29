import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from src.models.schemas import (
    FeatureInput, ChatData, ChatProgress, FeatureOverview, 
    Ticket, TicketsData, ConversationMessage, SessionDataWithConversation,
    AgentOutputData, HealthData, ClearSessionData, AgentOutput,
    HealthResponse, SessionWithConversationResponse, ClearSessionResponse
)
from src.models.agent_response import QuestionData


class TestFeatureInput:
    """Test the FeatureInput model."""
    
    def test_valid_feature_input(self):
        """Test creating a valid FeatureInput."""
        data = {
            "feature": "Create a user login system",
            "session_id": "test-session-123"
        }
        feature_input = FeatureInput(**data)
        
        assert feature_input.feature == "Create a user login system"
        assert feature_input.session_id == "test-session-123"
    
    def test_feature_input_without_session_id(self):
        """Test creating FeatureInput without session_id."""
        data = {"feature": "Create a user login system"}
        feature_input = FeatureInput(**data)
        
        assert feature_input.feature == "Create a user login system"
        assert feature_input.session_id is None
    
    def test_feature_input_empty_feature(self):
        """Test that empty feature is allowed (Pydantic default behavior)."""
        data = {"feature": ""}
        feature_input = FeatureInput(**data)
        
        assert feature_input.feature == ""
        assert feature_input.session_id is None
    
    def test_feature_input_missing_feature(self):
        """Test that missing feature raises validation error."""
        data = {}
        
        with pytest.raises(ValidationError):
            FeatureInput(**data)


class TestChatProgress:
    """Test the ChatProgress model."""
    
    def test_valid_chat_progress(self):
        """Test creating a valid ChatProgress."""
        progress = ChatProgress(answered_questions=2, total_questions=5)
        
        assert progress.answered_questions == 2
        assert progress.total_questions == 5
    
    def test_chat_progress_zero_values(self):
        """Test ChatProgress with zero values."""
        progress = ChatProgress(answered_questions=0, total_questions=0)
        
        assert progress.answered_questions == 0
        assert progress.total_questions == 0
    
    def test_chat_progress_negative_values(self):
        """Test that negative values are allowed (for edge cases)."""
        progress = ChatProgress(answered_questions=-1, total_questions=10)
        
        assert progress.answered_questions == -1
        assert progress.total_questions == 10


class TestChatData:
    """Test the ChatData model."""
    
    def test_valid_chat_data(self):
        """Test creating a valid ChatData."""
        data = {
            "response": "This is a test response",
            "questions": [
                {"question": "Question 1?", "status": "pending", "user_answer": None},
                {"question": "Question 2?", "status": "pending", "user_answer": None}
            ],
            "suggestions": ["Suggestion 1", "Suggestion 2"],
            "progress": ChatProgress(answered_questions=1, total_questions=2)
        }
        chat_data = ChatData(**data)
        
        assert chat_data.response == "This is a test response"
        assert len(chat_data.questions) == 2
        assert len(chat_data.suggestions) == 2
        assert chat_data.progress.answered_questions == 1
        assert chat_data.progress.total_questions == 2
    
    def test_chat_data_with_optional_fields_none(self):
        """Test ChatData with optional fields set to None."""
        data = {
            "response": "This is a test response",
            "questions": [
                {"question": "Question 1?", "status": "pending", "user_answer": None}
            ]
        }
        chat_data = ChatData(**data)
        
        assert chat_data.response == "This is a test response"
        assert len(chat_data.questions) == 1
        assert chat_data.suggestions is None
        assert chat_data.progress is None
    
    def test_chat_data_empty_questions(self):
        """Test ChatData with empty questions list."""
        data = {
            "response": "This is a test response",
            "questions": []
        }
        chat_data = ChatData(**data)
        
        assert chat_data.response == "This is a test response"
        assert chat_data.questions == []
    
    def test_chat_data_missing_required_fields(self):
        """Test that missing required fields raise validation error."""
        data = {"questions": [
            {"question": "Question 1?", "status": "pending", "user_answer": None}
        ]}
        with pytest.raises(Exception):
            ChatData(**data)


class TestFeatureOverview:
    """Test the FeatureOverview model."""
    
    def test_valid_feature_overview(self):
        """Test creating a valid FeatureOverview."""
        data = {
            "description": "A comprehensive user authentication system",
            "acceptance_criteria": [
                "Users can register with email and password",
                "Users can login with valid credentials"
            ],
            "progress_percentage": 75
        }
        feature_overview = FeatureOverview(**data)
        
        assert feature_overview.description == "A comprehensive user authentication system"
        assert len(feature_overview.acceptance_criteria) == 2
        assert feature_overview.progress_percentage == 75
    
    def test_feature_overview_empty_description(self):
        """Test FeatureOverview with empty description."""
        data = {
            "description": "",
            "acceptance_criteria": [],
            "progress_percentage": 0
        }
        feature_overview = FeatureOverview(**data)
        
        assert feature_overview.description == ""
        assert feature_overview.acceptance_criteria == []
        assert feature_overview.progress_percentage == 0
    
    def test_feature_overview_progress_percentage_bounds(self):
        """Test FeatureOverview with different progress percentage values."""
        # Test 0%
        data = {
            "description": "Test",
            "acceptance_criteria": [],
            "progress_percentage": 0
        }
        feature_overview = FeatureOverview(**data)
        assert feature_overview.progress_percentage == 0
        
        # Test 100%
        data["progress_percentage"] = 100
        feature_overview = FeatureOverview(**data)
        assert feature_overview.progress_percentage == 100
        
        # Test negative value (should be allowed for edge cases)
        data["progress_percentage"] = -10
        feature_overview = FeatureOverview(**data)
        assert feature_overview.progress_percentage == -10


class TestTicket:
    """Test the Ticket model."""
    
    def test_valid_ticket(self):
        """Test creating a valid Ticket."""
        data = {
            "title": "Implement user authentication",
            "description": "Create authentication service with JWT tokens",
            "technical_details": "Use bcrypt for password hashing",
            "acceptance_criteria": ["Service validates credentials", "Service generates JWT"],
            "cursor_prompt": "Create a new authentication service"
        }
        ticket = Ticket(**data)
        
        assert ticket.title == "Implement user authentication"
        assert ticket.description == "Create authentication service with JWT tokens"
        assert ticket.technical_details == "Use bcrypt for password hashing"
        assert len(ticket.acceptance_criteria) == 2
        assert ticket.cursor_prompt == "Create a new authentication service"
    
    def test_ticket_with_optional_fields_none(self):
        """Test Ticket with optional fields set to None."""
        data = {
            "title": "Implement user authentication",
            "description": "Create authentication service"
        }
        ticket = Ticket(**data)
        
        assert ticket.title == "Implement user authentication"
        assert ticket.description == "Create authentication service"
        assert ticket.technical_details is None
        assert ticket.acceptance_criteria is None
        assert ticket.cursor_prompt is None
    
    def test_ticket_missing_required_fields(self):
        """Test that missing required fields raise validation error."""
        data = {"title": "Test ticket"}
        
        with pytest.raises(ValidationError):
            Ticket(**data)


class TestTicketsData:
    """Test the TicketsData model."""
    
    def test_valid_tickets_data(self):
        """Test creating a valid TicketsData."""
        backend_ticket = Ticket(
            title="Backend ticket",
            description="Backend description"
        )
        frontend_ticket = Ticket(
            title="Frontend ticket",
            description="Frontend description"
        )
        
        data = {
            "backend": [backend_ticket],
            "frontend": [frontend_ticket]
        }
        tickets_data = TicketsData(**data)
        
        assert len(tickets_data.backend) == 1
        assert len(tickets_data.frontend) == 1
        assert tickets_data.backend[0].title == "Backend ticket"
        assert tickets_data.frontend[0].title == "Frontend ticket"
    
    def test_tickets_data_empty_arrays(self):
        """Test TicketsData with empty arrays."""
        data = {
            "backend": [],
            "frontend": []
        }
        tickets_data = TicketsData(**data)
        
        assert tickets_data.backend == []
        assert tickets_data.frontend == []


class TestConversationMessage:
    """Test the ConversationMessage model."""
    
    def test_valid_user_message(self):
        """Test creating a valid user message."""
        data = {
            "type": "user",
            "content": "Create a user login system",
            "timestamp": datetime.now(timezone.utc)
        }
        message = ConversationMessage(**data)
        
        assert message.type == "user"
        assert message.content == "Create a user login system"
        assert message.timestamp is not None
        assert message.chat is None
        assert message.feature_overview is None
        assert message.tickets is None
    
    def test_valid_assistant_message(self):
        """Test creating a valid assistant message."""
        chat_data = ChatData(
            response="I'll help you create a login system",
            questions=[{"question": "What authentication method do you prefer?", "status": "pending", "user_answer": None}]
        )
        feature_overview = FeatureOverview(
            description="User authentication system",
            acceptance_criteria=[],
            progress_percentage=0
        )
        tickets_data = TicketsData(backend=[], frontend=[])
        
        data = {
            "type": "assistant",
            "content": "Assistant response",
            "timestamp": datetime.now(timezone.utc),
            "chat": chat_data,
            "feature_overview": feature_overview,
            "tickets": tickets_data
        }
        message = ConversationMessage(**data)
        
        assert message.type == "assistant"
        assert message.content == "Assistant response"
        assert message.chat is not None
        assert message.feature_overview is not None
        assert message.tickets is not None
    
    def test_conversation_message_with_optional_fields_none(self):
        """Test ConversationMessage with optional fields set to None."""
        data = {
            "type": "user",
            "content": "Test message"
        }
        message = ConversationMessage(**data)
        
        assert message.type == "user"
        assert message.content == "Test message"
        assert message.timestamp is None
        assert message.chat is None
        assert message.feature_overview is None
        assert message.tickets is None


class TestSessionDataWithConversation:
    """Test the SessionDataWithConversation model."""
    
    def test_valid_session_data(self):
        """Test creating a valid SessionDataWithConversation."""
        conversation = [
            ConversationMessage(
                type="user",
                content="Create a login system"
            ),
            ConversationMessage(
                type="assistant",
                content="I'll help you"
            )
        ]
        
        data = {
            "session_id": "test-session-123",
            "title": "User Login System",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "conversation": conversation
        }
        session_data = SessionDataWithConversation(**data)
        
        assert session_data.session_id == "test-session-123"
        assert session_data.title == "User Login System"
        assert len(session_data.conversation) == 2
        assert session_data.conversation[0].type == "user"
        assert session_data.conversation[1].type == "assistant"
    
    def test_session_data_empty_conversation(self):
        """Test SessionDataWithConversation with empty conversation."""
        data = {
            "session_id": "test-session-123",
            "title": "User Login System",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "conversation": []
        }
        session_data = SessionDataWithConversation(**data)
        
        assert session_data.session_id == "test-session-123"
        assert session_data.conversation == []


class TestAgentOutputData:
    """Test the AgentOutputData model."""
    
    def test_valid_agent_output_data(self):
        """Test creating a valid AgentOutputData."""
        chat_data = ChatData(
            response="Test response",
            questions=[{"question": "Test question?", "status": "pending", "user_answer": None}]
        )
        feature_overview = FeatureOverview(
            description="Test description",
            acceptance_criteria=[],
            progress_percentage=0
        )
        tickets_data = TicketsData(backend=[], frontend=[])
        
        data = {
            "session_id": "test-session-123",
            "title": "Test Feature",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "chat": chat_data,
            "feature_overview": feature_overview,
            "tickets": tickets_data
        }
        agent_output = AgentOutputData(**data)
        
        assert agent_output.session_id == "test-session-123"
        assert agent_output.title == "Test Feature"
        assert agent_output.chat is not None
        assert agent_output.feature_overview is not None
        assert agent_output.tickets is not None


class TestResponseModels:
    """Test the response wrapper models."""
    
    def test_health_data(self):
        """Test HealthData model."""
        data = {
            "status": "healthy",
            "message": "Service is running"
        }
        health_data = HealthData(**data)
        
        assert health_data.status == "healthy"
        assert health_data.message == "Service is running"
    
    def test_clear_session_data(self):
        """Test ClearSessionData model."""
        data = {
            "message": "Session deleted successfully"
        }
        clear_data = ClearSessionData(**data)
        
        assert clear_data.message == "Session deleted successfully"
    
    def test_agent_output_success(self):
        """Test AgentOutput with success data."""
        chat_data = ChatData(
            response="Test response",
            questions=[]
        )
        feature_overview = FeatureOverview(
            description="Test",
            acceptance_criteria=[],
            progress_percentage=0
        )
        tickets_data = TicketsData(backend=[], frontend=[])
        
        agent_output_data = AgentOutputData(
            session_id="test-123",
            title="Test Feature",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            chat=chat_data,
            feature_overview=feature_overview,
            tickets=tickets_data
        )
        
        output = AgentOutput(data=agent_output_data, error=None)
        
        assert output.data is not None
        assert output.error is None
        assert output.data.title == "Test Feature"
    
    def test_agent_output_error(self):
        """Test AgentOutput with error."""
        from src.models.schemas import AgentOutputError
        
        error = AgentOutputError(
            type="security_rejection",
            message="Request rejected"
        )
        
        output = AgentOutput(data=None, error=error)
        
        assert output.data is None
        assert output.error is not None
        assert output.error.type == "security_rejection"
        assert output.error.message == "Request rejected" 