import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.main import app
from src.models.core_models import (
    FeatureInput, ChatData, ChatProgress, FeatureOverview, 
    Ticket, TicketsData, ConversationMessage,
    AgentResponse, AgentSuccessData, AgentError, SecurityResponse, QuestionData
)
from src.services.agent_service import AgentService
from src.services.session_service import SessionService
from src.services.health_service import HealthService


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_agent_service():
    """Create a mock agent service for testing."""
    mock_service = MagicMock(spec=AgentService)
    mock_service.process_feature = AsyncMock()
    return mock_service


@pytest.fixture
def mock_session_service():
    """Create a mock session service for testing."""
    mock_service = MagicMock(spec=SessionService)
    mock_service.get_session_with_conversation = MagicMock()
    mock_service.clear_session = MagicMock()
    return mock_service


@pytest.fixture
def mock_health_service():
    """Create a mock health service for testing."""
    mock_service = MagicMock(spec=HealthService)
    mock_service.check_health = AsyncMock()
    return mock_service


@pytest.fixture
def test_client(mock_agent_service, mock_session_service, mock_health_service) -> Generator:
    """Create a test client for FastAPI with dependency overrides."""
    # Override dependencies for testing
    from src.api import dependencies
    
    app.dependency_overrides = {
        dependencies.get_agent_service: lambda: mock_agent_service,
        dependencies.get_session_service: lambda: mock_session_service,
        dependencies.get_health_service: lambda: mock_health_service,
    }
    
    with TestClient(app) as client:
        yield client
    
    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(mock_agent_service, mock_session_service, mock_health_service) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for FastAPI with dependency overrides."""
    # Override dependencies for testing
    from src.api import dependencies
    
    app.dependency_overrides = {
        dependencies.get_agent_service: lambda: mock_agent_service,
        dependencies.get_session_service: lambda: mock_session_service,
        dependencies.get_health_service: lambda: mock_health_service,
    }
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def mock_ollama_response():
    """Mock Ollama response for testing."""
    return MagicMock(
        content="""RESPONSE:
This is a test response for the feature.

PENDING QUESTIONS:
- What is the primary use case?
- Who are the target users?

MARKDOWN:
# Feature: Test Feature

## Description
This is a test feature description.

## Acceptance Criteria
- Users can perform the main action
- System validates input correctly

## Backend Changes
- Implement core logic
- Add validation

## Frontend Changes
- Create user interface
- Add form validation"""
    )


@pytest.fixture
def sample_feature_input():
    """Sample feature input for testing."""
    return FeatureInput(
        feature="Create a user login system",
        session_id="test-session-123"
    )


@pytest.fixture
def sample_chat_data():
    """Sample chat data for testing."""
    return ChatData(
        response="This is a test response",
        questions=[
            QuestionData(question="Question 1?", status="pending", user_answer=None),
            QuestionData(question="Question 2?", status="pending", user_answer=None)
        ],
        suggestions=None,
        progress=ChatProgress(
            answered_questions=0,
            total_questions=2
        )
    )


@pytest.fixture
def sample_feature_overview():
    """Sample feature overview for testing."""
    return FeatureOverview(
        description="A comprehensive user authentication system",
        acceptance_criteria=[
            "Users can register with email and password",
            "Users can login with valid credentials",
            "System validates input and provides feedback"
        ],
        progress_percentage=0
    )


@pytest.fixture
def sample_tickets_data():
    """Sample tickets data for testing."""
    return TicketsData(
        backend=[
            Ticket(
                title="Implement user authentication logic",
                description="Create authentication service with JWT tokens",
                technical_details=None,
                acceptance_criteria=None,
                cursor_prompt=None
            )
        ],
        frontend=[
            Ticket(
                title="Create login form",
                description="Design and implement user login interface",
                technical_details=None,
                acceptance_criteria=None,
                cursor_prompt=None
            )
        ]
    )


@pytest.fixture
def sample_agent_success_response():
    """Sample successful agent response for testing."""
    return AgentResponse(
        data=AgentSuccessData(
            session_id="test-session-123",
            title="User Login System",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            response="This is a test response",
            markdown="# Feature: User Login System\n\n## Description\nTest description",
            questions=[
                QuestionData(question="Question 1?", status="pending", user_answer=None),
                QuestionData(question="Question 2?", status="pending", user_answer=None)
            ]
        )
    )


@pytest.fixture
def sample_agent_error_response():
    """Sample error agent response for testing."""
    return AgentResponse(
        error=AgentError(
            type="security_rejection",
            message="Request rejected by security agent"
        )
    )


@pytest.fixture
def sample_security_response():
    """Sample security response for testing."""
    return SecurityResponse(
        is_feature_request=True,
        confidence=0.95,
        reasoning="This is clearly a software feature request"
    )


@pytest.fixture
def mock_session_data():
    """Mock session data for testing."""
    return {
        "session_id": "test-session-123",
        "title": "User Login System",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "conversation": [
            {
                "type": "user",
                "content": "Create a user login system",
                "timestamp": datetime.now(timezone.utc)
            },
            {
                "type": "assistant",
                "response": "I'll help you create a user login system",
                "markdown": "# Feature: User Login System\n\n## Description\nTest description",
                "questions": [
                    {"question": "What authentication method do you prefer?", "status": "pending", "user_answer": None}
                ],
                "timestamp": datetime.now(timezone.utc)
            }
        ]
    }


@pytest.fixture
def mock_session_manager(mocker):
    """Mock session manager for testing."""
    mock_session = mocker.patch('src.core.session_manager.SessionManager')
    mock_instance = mock_session.return_value
    
    # Setup default mock behaviors
    mock_instance.session_exists.return_value = True
    mock_instance.get_session_title.return_value = "Test Feature"
    mock_instance.get_session_timestamps.return_value = (
        datetime.now(timezone.utc),
        datetime.now(timezone.utc)
    )
    mock_instance.get_chat_history.return_value = []
    mock_instance.get_session_with_conversation.return_value = {
        "session_id": "test-session-123",
        "title": "Test Feature",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "conversation": []
    }
    mock_instance.delete_session.return_value = True
    mock_instance.clear_session.return_value = True
    mock_instance.list_sessions.return_value = []
    
    return mock_instance


@pytest.fixture
def mock_ollama_client(mocker):
    """Mock Ollama client for testing."""
    mock_ollama = mocker.patch('langchain_ollama.chat_models.ChatOllama')
    mock_instance = mock_ollama.return_value
    mock_instance.ainvoke = AsyncMock()
    mock_instance.ainvoke.return_value = MagicMock(
        content="""RESPONSE:
Test response

PENDING QUESTIONS:
- Test question?

MARKDOWN:
# Feature: Test

## Description
Test description

## Acceptance Criteria
- Test criteria

## Backend Changes
- Test backend change

## Frontend Changes
- Test frontend change"""
    )
    return mock_instance 