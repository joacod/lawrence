"""
Health check routes for monitoring service status.
"""
from fastapi import APIRouter, Depends
from src.models.core_models import HealthResponse, HealthData
from src.services.health_service import HealthService
from src.api.dependencies import get_health_service

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(health_service: HealthService = Depends(get_health_service)):
    """Enhanced health check that includes Ollama connectivity"""
    try:
        health_status = await health_service.check_health()
        return HealthResponse(
            data=HealthData(**health_status),
            error=None
        )
    except Exception as e:
        # If health service itself fails, return unhealthy status
        return HealthResponse(
            data=HealthData(
                status="unhealthy",
                message="Service unavailable"
            ),
            error=None
        ) 