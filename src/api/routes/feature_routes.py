from fastapi import APIRouter, HTTPException
from src.models.schemas import FeatureInput, AgentOutput, HealthResponse
from src.services.agent_service import AgentService
from src.config.settings import settings

router = APIRouter()
agent_service = AgentService()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return {"status": "healthy", "service": settings.APP_NAME}

@router.post("/process_feature", response_model=AgentOutput)
async def process_feature(input: FeatureInput):
    try:
        session_id, title, response, markdown, questions, created_at, updated_at = await agent_service.process_feature(
            feature=input.feature,
            session_id=input.session_id
        )
        return AgentOutput(
            session_id=session_id,
            title=title,
            response=response,
            questions=questions,
            markdown=markdown,
            created_at=created_at,
            updated_at=updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear_session/{session_id}")
async def clear_session(session_id: str):
    if agent_service.clear_session(session_id):
        return {"message": f"Session {session_id} deleted"}
    raise HTTPException(status_code=404, detail="Session not found") 