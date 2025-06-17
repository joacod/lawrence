from pydantic import BaseModel
from typing import Optional, List

class FeatureInput(BaseModel):
    session_id: Optional[str] = None
    feature: str

class AgentOutput(BaseModel):
    session_id: str
    response: str
    questions: List[str]
    markdown: str

class HealthResponse(BaseModel):
    status: str
    service: str 