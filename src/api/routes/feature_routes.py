from fastapi import APIRouter, HTTPException
from src.models.schemas import FeatureInput, AgentOutput, AgentOutputData, AgentOutputError, HealthResponse
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
        
        # Convert AgentResponse to AgentOutput based on success/error
        if result.success:
            return AgentOutput(
                data=AgentOutputData(
                    session_id=result.data.session_id,
                    title=result.data.title,
                    response=result.data.response,
                    markdown=result.data.markdown,
                    questions=result.data.questions,
                    created_at=result.data.created_at,
                    updated_at=result.data.updated_at
                )
            )
        else:
            return AgentOutput(
                error=AgentOutputError(
                    type=result.error.type,
                    message=result.error.message
                )
            )
        
    except Exception as e:
        # This should rarely happen since AgentService now handles errors internally
        return AgentOutput(
            error=AgentOutputError(
                type="model_error",
                message=str(e)
            )
        )

@router.delete("/clear_session/{session_id}")
async def clear_session(session_id: str):
    if agent_service.clear_session(session_id):
        return {"message": f"Session {session_id} deleted"}
    raise HTTPException(status_code=404, detail="Session not found") 