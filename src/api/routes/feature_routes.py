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
        result = await agent_service.process_feature(
            feature=input.feature,
            session_id=input.session_id
        )
        
        # Convert AgentResponse to AgentOutput
        return AgentOutput(
            success=result.success,
            message=result.message,
            session_id=result.session_id,
            title=result.title,
            response=result.response,
            markdown=result.markdown,
            questions=result.questions,
            created_at=result.created_at,
            updated_at=result.updated_at,
            error_type=result.error_type
        )
        
    except Exception as e:
        # This should rarely happen since AgentService now handles errors internally
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear_session/{session_id}")
async def clear_session(session_id: str):
    if agent_service.clear_session(session_id):
        return {"message": f"Session {session_id} deleted"}
    raise HTTPException(status_code=404, detail="Session not found") 