"""
Dependency injection functions for FastAPI routes.
Centralizes all service dependencies for better maintainability.
"""
from src.services.agent_service import AgentService
from src.services.session_service import SessionService
from src.services.health_service import HealthService
from src.services.export_service import ExportService


def get_agent_service() -> AgentService:
    """Dependency to get agent service instance."""
    return AgentService()


def get_session_service() -> SessionService:
    """Dependency to get session service instance."""
    return SessionService()


def get_health_service() -> HealthService:
    """Dependency to get health service instance."""
    return HealthService()


def get_export_service() -> ExportService:
    """Dependency to get export service instance."""
    return ExportService() 