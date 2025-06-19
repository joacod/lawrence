from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime

class FeatureInput(BaseModel):
    session_id: Optional[str] = None
    feature: str

class AgentOutputData(BaseModel):
    """Structure for successful agent responses in API"""
    session_id: Optional[str] = None
    title: str
    response: str
    markdown: str
    questions: List[str]
    created_at: datetime
    updated_at: datetime

class AgentOutputError(BaseModel):
    """Structure for agent errors in API"""
    type: Literal["security_rejection", "parsing_error", "model_error"]
    message: str

class AgentOutput(BaseModel):
    """API response structure"""
    data: Optional[AgentOutputData] = None
    error: Optional[AgentOutputError] = None

class HealthResponse(BaseModel):
    status: str
    service: str 