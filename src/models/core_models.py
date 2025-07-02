from pydantic import BaseModel
from typing import Optional, List, Literal, Generic, TypeVar
from datetime import datetime

# Generic type variable for response data
T = TypeVar('T')

# =============================================================================
# CORE DATA MODELS
# =============================================================================

class QuestionData(BaseModel):
    """Structure for individual questions with their status and user answers"""
    question: str
    status: str  # "pending", "answered", "disregarded"
    user_answer: Optional[str] = None

class SecurityResponse(BaseModel):
    """Response structure for security agent analysis"""
    is_feature_request: bool
    confidence: float
    reasoning: str

# =============================================================================
# INPUT MODELS
# =============================================================================

class FeatureInput(BaseModel):
    """Input structure for feature processing requests"""
    session_id: Optional[str] = None
    feature: str

# =============================================================================
# ERROR MODELS
# =============================================================================

class AgentError(BaseModel):
    """Structure for agent errors"""
    type: Literal["security_rejection", "parsing_error", "internal_server_error", "not_found", "context_deviation"]
    message: str

# =============================================================================
# RESPONSE DATA MODELS
# =============================================================================

class ChatProgress(BaseModel):
    """Structure for chat progress tracking"""
    answered_questions: int
    total_questions: int

class ChatData(BaseModel):
    """Structure for chat section in response"""
    response: str
    questions: List[QuestionData]
    suggestions: Optional[List[str]] = None
    progress: Optional[ChatProgress] = None

class FeatureOverview(BaseModel):
    """Structure for feature overview section"""
    description: str
    acceptance_criteria: List[str]
    progress_percentage: int

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

class AgentSuccessData(BaseModel):
    """Structure for successful agent responses (internal format)"""
    session_id: Optional[str] = None
    title: str
    created_at: datetime
    updated_at: datetime
    response: str
    markdown: str
    questions: List[QuestionData]
    answered_questions: int = 0
    total_questions: int = 0

class AgentOutputData(BaseModel):
    """Structure for successful agent responses in API (external format)"""
    session_id: Optional[str] = None
    title: str
    created_at: datetime
    updated_at: datetime
    chat: ChatData
    feature_overview: FeatureOverview
    tickets: TicketsData

# =============================================================================
# CONVERSATION & SESSION MODELS
# =============================================================================

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

# =============================================================================
# UTILITY RESPONSE MODELS
# =============================================================================

class HealthData(BaseModel):
    """Structure for health check response data"""
    status: str
    message: str

class ClearSessionData(BaseModel):
    """Structure for clear session response data"""
    message: str

# =============================================================================
# GENERIC API RESPONSE WRAPPER
# =============================================================================

class ApiResponse(BaseModel, Generic[T]):
    """Generic API response structure with consistent data/error format"""
    data: Optional[T] = None
    error: Optional[AgentError] = None

class AgentResponse(BaseModel):
    """Base response structure for all agents (internal use)"""
    data: Optional[AgentSuccessData] = None
    error: Optional[AgentError] = None

    @property
    def success(self) -> bool:
        """Helper method to determine if the response was successful"""
        return self.data is not None and self.error is None

# =============================================================================
# SPECIFIC API RESPONSE TYPES
# =============================================================================

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