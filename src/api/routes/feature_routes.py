"""
Feature processing routes for handling AI-powered feature requests.
"""
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from src.models.core_models import (
    FeatureInput, AgentOutput, AgentOutputData, 
    ChatData, ChatProgress, FeatureOverview, TicketsData,
    ExportRequest, ExportResponse
)
from src.services.agent_service import AgentService
from src.services.export_service import ExportService
from src.api.dependencies import get_agent_service, get_export_service
from src.utils.parsers.markdown_parser import parse_markdown_sections
from src.utils.api.error_handlers import (
    create_error_response, create_service_unavailable_response
)
from src.utils.api.response_helpers import create_tickets_from_changes
import base64

router = APIRouter(tags=["features"])


@router.post("/process_feature", response_model=AgentOutput)
async def process_feature(
    input: FeatureInput, 
    agent_service: AgentService = Depends(get_agent_service)
):
    """Process a feature request using AI agents"""
    try:
        result = await agent_service.process_feature(
            feature=input.feature,
            session_id=input.session_id
        )
        
        # Convert AgentResponse to AgentOutput based on success/error
        if result.success:
            # Transform internal response to API format
            chat_data = ChatData(
                response=result.data.response,
                questions=result.data.questions,
                progress=ChatProgress(
                    answered_questions=getattr(result.data, 'answered_questions', 0),
                    total_questions=getattr(result.data, 'total_questions', len(result.data.questions))
                )
            )
            
            # Parse markdown to extract feature overview and tickets
            markdown_sections = parse_markdown_sections(result.data.markdown)
            
            # Create feature overview from parsed data
            # Calculate progress percentage based on answered questions
            answered_questions = getattr(result.data, 'answered_questions', 0)
            total_questions = getattr(result.data, 'total_questions', len(result.data.questions))
            progress_percentage = int((answered_questions / total_questions * 100) if total_questions > 0 else 0)
            
            feature_overview = FeatureOverview(
                description=markdown_sections.get("description", "Feature description will be implemented in future iterations"),
                acceptance_criteria=markdown_sections.get("acceptance_criteria", []),
                progress_percentage=progress_percentage
            )
            
            # Create backend tickets from parsed data
            backend_tickets = create_tickets_from_changes(markdown_sections.get("backend_changes", []))
            
            # Create frontend tickets from parsed data
            frontend_tickets = create_tickets_from_changes(markdown_sections.get("frontend_changes", []))
            
            tickets = TicketsData(
                backend=backend_tickets,
                frontend=frontend_tickets
            )
            
            return AgentOutput(
                data=AgentOutputData(
                    session_id=result.data.session_id,
                    title=result.data.title,
                    created_at=result.data.created_at,
                    updated_at=result.data.updated_at,
                    chat=chat_data,
                    feature_overview=feature_overview,
                    tickets=tickets
                ),
                error=None
            )
        else:
            return create_error_response(
                response_model=AgentOutput,
                error_type=result.error.type,
                error_message=result.error.message
            )
            
    except Exception as e:
        # Handle unexpected exceptions
        return create_service_unavailable_response(
            response_model=AgentOutput,
            message="An internal error occurred"
        )


@router.post("/export_feature", response_model=ExportResponse)
async def export_feature(
    request: ExportRequest,
    export_service: ExportService = Depends(get_export_service)
):
    """Export feature data to Markdown or PDF format"""
    try:
        export_data, error = await export_service.export_feature(
            session_id=request.session_id,
            export_format=request.format
        )
        
        if error:
            return create_error_response(
                response_model=ExportResponse,
                error_type=error.type,
                error_message=error.message
            )
        
        return ExportResponse(
            data=export_data,
            error=None
        )
        
    except Exception as e:
        return create_service_unavailable_response(
            response_model=ExportResponse,
            message="An internal error occurred during export"
        )