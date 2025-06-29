from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel

class AgentSuccessData(BaseModel):
    """Structure for successful agent responses"""
    session_id: Optional[str] = None
    title: str
    created_at: datetime
    updated_at: datetime
    response: str
    markdown: str
    questions: List[str]

class AgentError(BaseModel):
    """Structure for agent errors"""
    type: Literal["security_rejection", "parsing_error", "internal_server_error", "context_deviation"]
    message: str

class AgentResponse(BaseModel):
    """Base response structure for all agents"""
    data: Optional[AgentSuccessData] = None
    error: Optional[AgentError] = None

    @property
    def success(self) -> bool:
        """Helper method to determine if the response was successful"""
        return self.data is not None and self.error is None

class SecurityResponse(BaseModel):
    """Response structure for security agent"""
    is_feature_request: bool
    confidence: float
    reasoning: str 