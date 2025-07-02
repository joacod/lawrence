from typing import Optional, Dict, Any, Type, TypeVar
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from src.models.core_models import AgentError

T = TypeVar('T', bound=BaseModel)

# Error type to HTTP status code mapping
ERROR_STATUS_CODE_MAP = {
    "security_rejection": 400,
    "context_deviation": 400,
    "not_found": 404,
    "internal_server_error": 500,
    "parsing_error": 400,
}

DEFAULT_ERROR_STATUS_CODE = 500

def get_status_code_for_error_type(error_type: str) -> int:
    """Get the appropriate HTTP status code for an error type."""
    return ERROR_STATUS_CODE_MAP.get(error_type, DEFAULT_ERROR_STATUS_CODE)

def create_error_response(
    response_model: Type[T],
    error_type: str,
    error_message: str,
    status_code: Optional[int] = None
) -> JSONResponse:
    """
    Create a standardized error JSON response.
    
    Args:
        response_model: The Pydantic model class for the response
        error_type: The type of error (used for status code mapping if status_code not provided)
        error_message: Human-readable error message
        status_code: Optional explicit status code, otherwise derived from error_type
    
    Returns:
        JSONResponse with the error formatted according to the response model
    """
    if status_code is None:
        status_code = get_status_code_for_error_type(error_type)
    
    # Create the response using the model structure
    error_response = response_model(
        data=None,
        error=AgentError(
            type=error_type,
            message=error_message
        )
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump()
    )

def create_not_found_response(
    response_model: Type[T],
    resource_name: str = "Resource"
) -> JSONResponse:
    """Create a standardized 404 not found response."""
    return create_error_response(
        response_model=response_model,
        error_type="not_found",
        error_message=f"{resource_name} not found",
        status_code=404
    )

def create_service_unavailable_response(
    response_model: Type[T],
    message: str = "Service temporarily unavailable"
) -> JSONResponse:
    """Create a standardized 503 service unavailable response."""
    return create_error_response(
        response_model=response_model,
        error_type="internal_server_error",
        error_message=message,
        status_code=503
    )

def create_internal_error_response(
    response_model: Type[T],
    message: str = "An internal error occurred"
) -> JSONResponse:
    """Create a standardized 500 internal server error response."""
    return create_error_response(
        response_model=response_model,
        error_type="internal_server_error",
        error_message=message,
        status_code=500
    ) 