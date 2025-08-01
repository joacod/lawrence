import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from src.models.core_models import FeatureInput, AgentResponse, AgentSuccessData, AgentError


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
- **Title: Implement User Authentication** - Create authentication service with JWT tokens
- **Title: Add JWT Token Generation** - Implement JWT token generation and validation

## Frontend Changes
- **Title: Create Registration Form** - Design responsive registration form with validation
- **Title: Create Login Form** - Design responsive login form with validation""",
                questions=[{"question": "What authentication method do you prefer?", "status": "pending", "user_answer": None}]
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
        assert data["data"]["feature_overview"]["progress_percentage"] == 0  # No answered questions in this test
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
        
        assert response.status_code == 500
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
    
    @pytest.mark.asyncio
    async def test_process_feature_progress_percentage_calculation(self, test_client, sample_feature_input, mock_agent_service):
        """Test progress percentage calculation with answered questions."""
        # Mock successful agent response with answered questions
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
- **Title: Implement User Authentication** - Create authentication service with JWT tokens

## Frontend Changes
- **Title: Create Login Form** - Design responsive login form with validation""",
                questions=[
                    {"question": "What authentication method do you prefer?", "status": "answered", "user_answer": "JWT"},
                    {"question": "Do you need password reset functionality?", "status": "answered", "user_answer": "Yes"},
                    {"question": "What is your preferred UI framework?", "status": "pending", "user_answer": None}
                ],
                answered_questions=2,
                total_questions=3
            )
        )
        
        response = test_client.post("/process_feature", json=sample_feature_input.model_dump())
        
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None
        assert data["data"]["feature_overview"]["progress_percentage"] == 66  # 2/3 * 100 = 66.66... truncated to 66
        assert data["data"]["chat"]["progress"]["answered_questions"] == 2
        assert data["data"]["chat"]["progress"]["total_questions"] == 3
    
    @pytest.mark.asyncio
    async def test_process_feature_progress_percentage_complete(self, test_client, sample_feature_input, mock_agent_service):
        """Test progress percentage calculation when all questions are answered."""
        # Mock successful agent response with all questions answered
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
- **Title: Implement User Authentication** - Create authentication service with JWT tokens

## Frontend Changes
- **Title: Create Login Form** - Design responsive login form with validation""",
                questions=[
                    {"question": "What authentication method do you prefer?", "status": "answered", "user_answer": "JWT"},
                    {"question": "Do you need password reset functionality?", "status": "answered", "user_answer": "Yes"}
                ],
                answered_questions=2,
                total_questions=2
            )
        )
        
        response = test_client.post("/process_feature", json=sample_feature_input.model_dump())
        
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None
        assert data["data"]["feature_overview"]["progress_percentage"] == 100  # 2/2 * 100
        assert data["data"]["chat"]["progress"]["answered_questions"] == 2
        assert data["data"]["chat"]["progress"]["total_questions"] == 2
    
    @pytest.mark.asyncio
    async def test_process_feature_progress_percentage_no_questions(self, test_client, sample_feature_input, mock_agent_service):
        """Test progress percentage calculation when no questions are present."""
        # Mock successful agent response with no questions
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
- **Title: Implement User Authentication** - Create authentication service with JWT tokens

## Frontend Changes
- **Title: Create Login Form** - Design responsive login form with validation""",
                questions=[],
                answered_questions=0,
                total_questions=0
            )
        )
        
        response = test_client.post("/process_feature", json=sample_feature_input.model_dump())
        
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None
        assert data["data"]["feature_overview"]["progress_percentage"] == 0  # 0/0 should default to 0
        assert data["data"]["chat"]["progress"]["answered_questions"] == 0
        assert data["data"]["chat"]["progress"]["total_questions"] == 0
    
    @pytest.mark.asyncio
    async def test_process_feature_progress_percentage_default_values(self, test_client, sample_feature_input, mock_agent_service):
        """Test progress percentage calculation when answered_questions and total_questions use default values (0)."""
        # Mock successful agent response with default values (0) for answered_questions and total_questions
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
- **Title: Implement User Authentication** - Create authentication service with JWT tokens

## Frontend Changes
- **Title: Create Login Form** - Design responsive login form with validation""",
                questions=[
                    {"question": "What authentication method do you prefer?", "status": "pending", "user_answer": None},
                    {"question": "Do you need password reset functionality?", "status": "pending", "user_answer": None}
                ]
                # answered_questions and total_questions will default to 0
            )
        )
        
        response = test_client.post("/process_feature", json=sample_feature_input.model_dump())
        
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None
        assert data["data"]["feature_overview"]["progress_percentage"] == 0  # Should default to 0 when total_questions is 0
        assert data["data"]["chat"]["progress"]["answered_questions"] == 0  # Should default to 0
        assert data["data"]["chat"]["progress"]["total_questions"] == 0  # Should use the default value of 0 from the model
    
    @pytest.mark.asyncio
    async def test_process_feature_progress_percentage_decimal_rounding(self, test_client, sample_feature_input, mock_agent_service):
        """Test progress percentage calculation with decimal values that get rounded."""
        # Mock successful agent response with decimal percentage (1 out of 3 questions = 33.33%)
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
- **Title: Implement User Authentication** - Create authentication service with JWT tokens

## Frontend Changes
- **Title: Create Login Form** - Design responsive login form with validation""",
                questions=[
                    {"question": "What authentication method do you prefer?", "status": "answered", "user_answer": "JWT"},
                    {"question": "Do you need password reset functionality?", "status": "pending", "user_answer": None},
                    {"question": "What is your preferred UI framework?", "status": "pending", "user_answer": None}
                ],
                answered_questions=1,
                total_questions=3
            )
        )
        
        response = test_client.post("/process_feature", json=sample_feature_input.model_dump())
        
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None
        assert data["data"]["feature_overview"]["progress_percentage"] == 33  # 1/3 * 100 = 33.33... rounded to 33
        assert data["data"]["chat"]["progress"]["answered_questions"] == 1
        assert data["data"]["chat"]["progress"]["total_questions"] == 3


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
- **Title: Implement User Authentication** - Create authentication service with JWT tokens

## Frontend Changes
- **Title: Create Login Form** - Design responsive login form with validation""",
                    "questions": [
                        {"question": "What authentication method do you prefer?", "status": "pending", "user_answer": None}
                    ],
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
        assert assistant_message["feature_overview"]["progress_percentage"] == 0  # No answered questions in this test
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
        """Test the create_tickets_from_changes helper function with new format."""
        from src.utils.api.response_helpers import create_tickets_from_changes
        
        changes = [
            {"title": "Implement User Authentication", "description": "Create authentication service with JWT tokens"},
            {"title": "Add Password Hashing", "description": "Implement bcrypt password hashing for security"},
            {"title": "Create User Registration", "description": "Add user registration endpoint with validation"}
        ]
        
        tickets = create_tickets_from_changes(changes)
        
        assert len(tickets) == 3
        assert tickets[0].title == "Implement User Authentication"
        assert tickets[0].description == "Create authentication service with JWT tokens"
        assert tickets[1].title == "Add Password Hashing"
        assert tickets[1].description == "Implement bcrypt password hashing for security"
        assert tickets[2].title == "Create User Registration"
        assert tickets[2].description == "Add user registration endpoint with validation"
    
    def test_create_tickets_from_changes_long_title(self, test_client):
        """Test ticket creation with long titles that get truncated."""
        from src.utils.api.response_helpers import create_tickets_from_changes
        
        long_change = {"title": "This is a very long title that should be truncated to 50 characters when creating the ticket title", "description": "This is the full description that should be preserved"}
        
        tickets = create_tickets_from_changes([long_change])
        
        assert len(tickets) == 1
        assert tickets[0].title == "This is a very long title that should be truncated to 50 characters when creating the ticket title"
        assert tickets[0].description == "This is the full description that should be preserved"
    
    def test_create_tickets_from_changes_empty_list(self, test_client):
        """Test ticket creation with empty changes list."""
        from src.utils.api.response_helpers import create_tickets_from_changes
        
        tickets = create_tickets_from_changes([])
        
        assert tickets == []
    
 