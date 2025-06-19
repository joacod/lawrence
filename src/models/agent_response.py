from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel

class AgentResponse(BaseModel):
    """Base response structure for all agents"""
    success: bool
    message: str
    session_id: Optional[str] = None
    title: Optional[str] = None
    response: Optional[str] = None
    markdown: Optional[str] = None
    questions: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    error_type: Optional[Literal["security_rejection", "parsing_error", "model_error"]] = None

class SecurityResponse(BaseModel):
    """Response structure for security agent"""
    is_feature_request: bool
    confidence: float
    reasoning: str 