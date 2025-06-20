from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime

class FeatureInput(BaseModel):
    session_id: Optional[str] = None
    feature: str

class AgentOutputError(BaseModel):
    """Structure for agent errors in API"""
    type: Literal["security_rejection", "parsing_error", "internal_server_error", "not_found"]
    message: str

class ConversationMessage(BaseModel):
    """Structure for individual conversation messages"""
    type: str  # "user" or "assistant"
    content: Optional[str] = None
    response: Optional[str] = None
    markdown: Optional[str] = None
    questions: Optional[List[str]] = None
    timestamp: Optional[datetime] = None

class SessionDataWithConversation(BaseModel):
    """Structure for session data including full conversation history"""
    session_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    conversation: List[ConversationMessage]

class SessionWithConversationResponse(BaseModel):
    """Response structure for GET session endpoint with conversation history"""
    data: List[SessionDataWithConversation]
    error: Optional[AgentOutputError] = None

class AgentOutputData(BaseModel):
    """Structure for successful agent responses in API"""
    session_id: Optional[str] = None
    title: str
    response: str
    markdown: str
    questions: List[str]
    created_at: datetime
    updated_at: datetime

class AgentOutput(BaseModel):
    """API response structure"""
    data: Optional[AgentOutputData] = None
    error: Optional[AgentOutputError] = None

class HealthResponse(BaseModel):
    status: str
    service: str 