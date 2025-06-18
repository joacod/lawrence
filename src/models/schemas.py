from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class FeatureInput(BaseModel):
    session_id: Optional[str] = None
    feature: str

class AgentOutput(BaseModel):
    session_id: str
    title: str
    response: str
    questions: List[str]
    markdown: str
    created_at: datetime
    updated_at: datetime

class HealthResponse(BaseModel):
    status: str
    service: str 