import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from src.models.schemas import FeatureInput
from src.models.agent_response import AgentResponse, AgentSuccessData, AgentError


class TestHealthEndpoint:
    """Test the health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, test_client, mock_health_service):
        """Test successful health check."""
        # Mock successful health check
        mock_health_service.check_health.return_value = {
            "status": "healthy",
            "message": "Service up and running"
        }
        
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "healthy"
        assert data["data"]["message"] == "Service up and running"
        assert data["error"] is None
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, test_client, mock_health_service):
        """Test health check when Ollama is unavailable."""
        # Mock health service to return unhealthy status
        mock_health_service.check_health.return_value = {
            "status": "unhealthy",
            "message": "Ollama connection failed"
        }
        
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "unhealthy"
        assert data["data"]["message"] == "Ollama connection failed"
        assert data["error"] is None


class TestProcessFeatureEndpoint:
    """Test the process feature endpoint."""
    
    @pytest.mark.asyncio
    async def test_process_feature_success(self, test_client, sample_feature_input, mock_agent_service):
        """Test successful feature processing."""
        # Mock successful agent response
        mock_agent_service.process_feature.return_value = AgentResponse(
            data=AgentSuccessData(
                session_id="test-session-123",
                title="User Login System",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                response="I'll help you create a user login system",
                markdown="""# Feature: User Login System

## Description
A comprehensive user authentication system.

## Acceptance Criteria
- Users can register with email and password
- Users can login with valid credentials

## Backend Changes
- Implement user authentication service
- Add JWT token generation

## Frontend Changes
- Create registration form
- Create login form""",
                questions=["What authentication method do you prefer?"]
            )
        )
        
        response = test_client.post("/process_feature", json=sample_feature_input.model_dump())
        
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None
        assert data["data"]["session_id"] == "test-session-123"
        assert data["data"]["title"] == "User Login System"
        assert data["data"]["chat"]["response"] == "I'll help you create a user login system"
        assert len(data["data"]["chat"]["questions"]) == 1
        assert data["data"]["feature_overview"]["description"] == "A comprehensive user authentication system."
        assert len(data["data"]["feature_overview"]["acceptance_criteria"]) == 2
        assert len(data["data"]["tickets"]["backend"]) == 2
        assert len(data["data"]["tickets"]["frontend"]) == 2
    
    @pytest.mark.asyncio
    async def test_process_feature_security_rejection(self, test_client, sample_feature_input, mock_agent_service):
        """Test feature processing with security rejection."""
        # Mock security rejection
        mock_agent_service.process_feature.return_value = AgentResponse(
            error=AgentError(
                type="security_rejection",
                message="Request rejected by security agent"
            )
        )
        
        response = test_client.post("/process_feature", json=sample_feature_input.model_dump())
        
        assert response.status_code == 400
        data = response.json()
        assert data["data"] is None
        assert data["error"]["type"] == "security_rejection"
        assert data["error"]["message"] == "Request rejected by security agent"
    
    @pytest.mark.asyncio
    async def test_process_feature_internal_error(self, test_client, sample_feature_input, mock_agent_service):
        """Test feature processing with internal error."""
        # Mock internal error
        mock_agent_service.process_feature.return_value = AgentResponse(
            error=AgentError(
                type="internal_server_error",
                message="An internal error occurred"
            )
        )
        
        response = test_client.post("/process_feature", json=sample_feature_input.model_dump())
        
        assert response.status_code == 503
        data = response.json()
        assert data["data"] is None
        assert data["error"]["type"] == "internal_server_error"
    
    @pytest.mark.asyncio
    async def test_process_feature_invalid_input(self, test_client, mock_agent_service):
        """Test feature processing with invalid input."""
        # Test missing feature
        response = test_client.post("/process_feature", json={})
        assert response.status_code == 422
        
        # Test empty feature - currently the model doesn't validate empty strings, but security agent rejects them
        mock_agent_service.process_feature.return_value = AgentResponse(
            error=AgentError(
                type="security_rejection",
                message="Request rejected by security agent"
            )
        )
        response = test_client.post("/process_feature", json={"feature": ""})
        assert response.status_code == 400  # Security agent rejects empty feature requests
    
    @pytest.mark.asyncio
    async def test_process_feature_agent_service_exception(self, test_client, sample_feature_input, mock_agent_service):
        """Test feature processing when agent service raises an exception."""
        # Mock agent service to raise exception
        mock_agent_service.process_feature.side_effect = Exception("Unexpected error")
        
        response = test_client.post("/process_feature", json=sample_feature_input.model_dump())
        
        assert response.status_code == 503
        data = response.json()
        assert data["data"] is None
        assert data["error"]["type"] == "internal_server_error"


class TestGetSessionEndpoint:
    """Test the get session endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_session_success(self, test_client, mock_session_data, mock_session_service):
        """Test successful session retrieval."""
        # Mock session service
        mock_session_service.get_session_with_conversation.return_value = mock_session_data
        
        response = test_client.get("/session/test-session-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None
        assert len(data["data"]) == 1
        session = data["data"][0]
        assert session["session_id"] == "test-session-123"
        assert session["title"] == "User Login System"
        assert len(session["conversation"]) == 2
        assert session["conversation"][0]["type"] == "user"
        assert session["conversation"][1]["type"] == "assistant"
    
    @pytest.mark.asyncio
    async def test_get_session_not_found(self, test_client, mock_session_service):
        """Test session retrieval when session doesn't exist."""
        # Mock session service to return None
        mock_session_service.get_session_with_conversation.return_value = None
        
        response = test_client.get("/session/nonexistent-session")
        
        assert response.status_code == 404
        data = response.json()
        assert data["data"] is None
        assert data["error"]["type"] == "not_found"
        assert data["error"]["message"] == "Session not found"
    
    @pytest.mark.asyncio
    async def test_get_session_with_assistant_message_parsing(self, test_client, mock_session_service):
        """Test session retrieval with proper assistant message parsing."""
        # Create session data with assistant message containing markdown
        session_data = {
            "session_id": "test-session-123",
            "title": "User Login System",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "conversation": [
                {
                    "type": "user",
                    "content": "Create a login system",
                    "timestamp": datetime.now(timezone.utc)
                },
                {
                    "type": "assistant",
                    "response": "I'll help you create a login system",
                    "markdown": """# Feature: User Login System

## Description
A comprehensive user authentication system.

## Acceptance Criteria
- Users can register with email and password
- Users can login with valid credentials

## Backend Changes
- Implement user authentication service

## Frontend Changes
- Create login form""",
                    "questions": ["What authentication method do you prefer?"],
                    "timestamp": datetime.now(timezone.utc)
                }
            ]
        }
        
        # Mock session service
        mock_session_service.get_session_with_conversation.return_value = session_data
        
        response = test_client.get("/session/test-session-123")
        
        assert response.status_code == 200
        data = response.json()
        session = data["data"][0]
        
        # Check user message
        user_message = session["conversation"][0]
        assert user_message["type"] == "user"
        assert user_message["chat"] is None
        assert user_message["feature_overview"] is None
        assert user_message["tickets"] is None
        
        # Check assistant message
        assistant_message = session["conversation"][1]
        assert assistant_message["type"] == "assistant"
        assert assistant_message["chat"] is not None
        assert assistant_message["chat"]["response"] == "I'll help you create a login system"
        assert len(assistant_message["chat"]["questions"]) == 1
        assert assistant_message["feature_overview"] is not None
        assert assistant_message["feature_overview"]["description"] == "A comprehensive user authentication system."
        assert assistant_message["tickets"] is not None
        assert len(assistant_message["tickets"]["backend"]) == 1
        assert len(assistant_message["tickets"]["frontend"]) == 1


class TestClearSessionEndpoint:
    """Test the clear session endpoint."""
    
    @pytest.mark.asyncio
    async def test_clear_session_success(self, test_client, mock_session_service):
        """Test successful session clearing."""
        # Mock session service
        mock_session_service.clear_session.return_value = True
        
        response = test_client.delete("/clear_session/test-session-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None
        assert data["data"]["message"] == "Session test-session-123 deleted"
    
    @pytest.mark.asyncio
    async def test_clear_session_not_found(self, test_client, mock_session_service):
        """Test session clearing when session doesn't exist."""
        # Mock session service to return False
        mock_session_service.clear_session.return_value = False
        
        response = test_client.delete("/clear_session/nonexistent-session")
        
        assert response.status_code == 404
        data = response.json()
        assert data["data"] is None
        assert data["error"]["type"] == "not_found"
        assert data["error"]["message"] == "Session not found"


class TestHelperFunctions:
    """Test the helper functions in feature routes."""
    
    def test_create_tickets_from_changes(self, test_client):
        """Test the _create_tickets_from_changes helper function."""
        from src.api.routes.feature_routes import _create_tickets_from_changes
        
        changes = [
            "Implement user authentication service with JWT tokens",
            "Add password hashing with bcrypt",
            "Create user registration endpoint"
        ]
        
        tickets = _create_tickets_from_changes(changes)
        
        assert len(tickets) == 3
        assert tickets[0].title == "Implement user authentication service with JWT tok..."
        assert tickets[0].description == "Implement user authentication service with JWT tokens"
        assert tickets[1].title == "Add password hashing with bcrypt"
        assert tickets[2].title == "Create user registration endpoint"
    
    def test_create_tickets_from_changes_long_title(self, test_client):
        """Test ticket creation with long titles that get truncated."""
        from src.api.routes.feature_routes import _create_tickets_from_changes
        
        long_change = "This is a very long change description that should be truncated to 50 characters when creating the ticket title"
        
        tickets = _create_tickets_from_changes([long_change])
        
        assert len(tickets) == 1
        assert tickets[0].title == "This is a very long change description that should..."
        assert tickets[0].description == long_change  # Full description preserved
    
    def test_create_tickets_from_changes_empty_list(self, test_client):
        """Test ticket creation with empty changes list."""
        from src.api.routes.feature_routes import _create_tickets_from_changes
        
        tickets = _create_tickets_from_changes([])
        
        assert tickets == [] 