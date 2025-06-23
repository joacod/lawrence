import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.main import app
from src.models.schemas import (
    FeatureInput, ChatData, ChatProgress, FeatureOverview, 
    Ticket, TicketsData, ConversationMessage
)
from src.models.agent_response import AgentResponse, AgentSuccessData, AgentError, SecurityResponse


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client() -> Generator:
    """Create a test client for FastAPI."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for FastAPI."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


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
        questions=["Question 1?", "Question 2?"],
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
            questions=["Question 1?", "Question 2?"]
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
                "questions": ["What authentication method do you prefer?"],
                "timestamp": datetime.now(timezone.utc)
            }
        ]
    }


@pytest.fixture
def mock_storage_manager(mocker):
    """Mock storage manager for testing."""
    mock_storage = mocker.patch('src.core.storage_manager.StorageManager')
    mock_instance = mock_storage.return_value
    
    # Setup default mock behaviors
    mock_instance.session_exists.return_value = True
    mock_instance.get_session_title.return_value = "Test Feature"
    mock_instance.get_session_timestamps.return_value = {
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    mock_instance.get_chat_history.return_value = []
    mock_instance.get_all_session_data.return_value = {
        "session_id": "test-session-123",
        "title": "Test Feature",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "conversation": []
    }
    mock_instance.delete_session.return_value = True
    
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