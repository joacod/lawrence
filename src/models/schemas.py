from pydantic import BaseModel
from typing import Optional, List, Literal, Generic, TypeVar
from datetime import datetime

# Generic type variable for response data
T = TypeVar('T')

class FeatureInput(BaseModel):
    session_id: Optional[str] = None
    feature: str

class AgentOutputError(BaseModel):
    """Structure for agent errors in API"""
    type: Literal["security_rejection", "parsing_error", "internal_server_error", "not_found"]
    message: str

# Chat section structure
class ChatProgress(BaseModel):
    """Structure for chat progress tracking"""
    answered_questions: int
    total_questions: int

class ChatData(BaseModel):
    """Structure for chat section in response"""
    response: str
    questions: List[str]
    suggestions: Optional[List[str]] = None
    progress: Optional[ChatProgress] = None

# Feature Overview section structure
class FeatureOverview(BaseModel):
    """Structure for feature overview section"""
    description: str
    acceptance_criteria: List[str]
    progress_percentage: int

# Tickets section structure
class Ticket(BaseModel):
    """Structure for individual tickets"""
    title: str
    description: str
    technical_details: Optional[str] = None
    acceptance_criteria: Optional[List[str]] = None
    cursor_prompt: Optional[str] = None

class TicketsData(BaseModel):
    """Structure for tickets section"""
    backend: List[Ticket]
    frontend: List[Ticket]

class ConversationMessage(BaseModel):
    """Structure for individual conversation messages"""
    type: str  # "user" or "assistant"
    content: Optional[str] = None
    timestamp: Optional[datetime] = None
    chat: Optional[ChatData] = None
    feature_overview: Optional[FeatureOverview] = None
    tickets: Optional[TicketsData] = None

class SessionDataWithConversation(BaseModel):
    """Structure for session data including full conversation history"""
    session_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    conversation: List[ConversationMessage]

class AgentOutputData(BaseModel):
    """Structure for successful agent responses in API"""
    session_id: Optional[str] = None
    title: str
    created_at: datetime
    updated_at: datetime
    chat: ChatData
    feature_overview: FeatureOverview
    tickets: TicketsData

class HealthData(BaseModel):
    """Structure for health check response data"""
    status: str
    message: str

class ClearSessionData(BaseModel):
    """Structure for clear session response data"""
    message: str

# Generic response wrapper
class ApiResponse(BaseModel, Generic[T]):
    """Generic API response structure with consistent data/error format"""
    data: Optional[T] = None
    error: Optional[AgentOutputError] = None

# Specific response types using the generic wrapper
class HealthResponse(ApiResponse[HealthData]):
    """Response structure for health check endpoint"""
    pass

class SessionWithConversationResponse(ApiResponse[List[SessionDataWithConversation]]):
    """Response structure for GET session endpoint with conversation history"""
    pass

class AgentOutput(ApiResponse[AgentOutputData]):
    """API response structure for agent operations"""
    pass

class ClearSessionResponse(ApiResponse[ClearSessionData]):
    """Response structure for clear session endpoint"""
    pass 