from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from src.models.schemas import (
    FeatureInput, AgentOutput, AgentOutputData, AgentOutputError, 
    HealthResponse, HealthData, SessionWithConversationResponse, 
    SessionDataWithConversation, ConversationMessage, ClearSessionResponse, ClearSessionData,
    ChatData, ChatProgress, FeatureOverview, TicketsData, Ticket
)
from src.services.agent_service import AgentService
from src.services.session_service import SessionService
from src.services.health_service import HealthService
from src.utils.response_parser import parse_markdown_sections
from src.config.settings import settings

router = APIRouter()
agent_service = AgentService()
session_service = SessionService()
health_service = HealthService()

@router.get("/health", response_model=HealthResponse)
async def health_check():
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

@router.get("/session/{session_id}", response_model=SessionWithConversationResponse)
async def get_session(session_id: str):
    """Get a specific session by session_id with full conversation history"""
    session_data = session_service.get_session_with_conversation(session_id)
    
    if not session_data:
        return JSONResponse(
            status_code=404,
            content=SessionWithConversationResponse(
                data=None,
                error=AgentOutputError(
                    type="not_found",
                    message="Session not found"
                )
            ).model_dump()
        )
    
    # Convert conversation data to proper schema format
    conversation_messages = []
    
    for msg in session_data["conversation"]:
        if msg["type"] == "user":
            # User messages - set structured data to null
            conversation_messages.append(ConversationMessage(
                type=msg["type"],
                content=msg.get("content"),
                timestamp=msg.get("timestamp"),
                chat=None,
                feature_overview=None,
                tickets=None
            ))
            
        elif msg["type"] == "assistant":
            # Assistant messages - parse the markdown and create full structure
            markdown = msg.get("markdown", "")
            response = msg.get("response", "")
            questions = msg.get("questions", [])
            
            # Parse markdown to extract feature overview and tickets
            markdown_sections = parse_markdown_sections(markdown)
            
            # Create chat data
            chat_data = ChatData(
                response=response,
                questions=questions,
                suggestions=None,
                progress=ChatProgress(
                    answered_questions=0,
                    total_questions=len(questions)
                )
            )
            
            # Create feature overview from parsed data
            feature_overview = FeatureOverview(
                description=markdown_sections.get("description", ""),
                acceptance_criteria=markdown_sections.get("acceptance_criteria", []),
                progress_percentage=0
            )
            
            # Create backend tickets from parsed data
            backend_tickets = []
            for backend_change in markdown_sections.get("backend_changes", []):
                backend_tickets.append(Ticket(
                    title=backend_change[:50] + "..." if len(backend_change) > 50 else backend_change,
                    description=backend_change,
                    technical_details=None,
                    acceptance_criteria=None,
                    cursor_prompt=None
                ))
            
            # Create frontend tickets from parsed data
            frontend_tickets = []
            for frontend_change in markdown_sections.get("frontend_changes", []):
                frontend_tickets.append(Ticket(
                    title=frontend_change[:50] + "..." if len(frontend_change) > 50 else frontend_change,
                    description=frontend_change,
                    technical_details=None,
                    acceptance_criteria=None,
                    cursor_prompt=None
                ))
            
            tickets = TicketsData(
                backend=backend_tickets,
                frontend=frontend_tickets
            )
            
            conversation_messages.append(ConversationMessage(
                type=msg["type"],
                content=msg.get("content"),
                timestamp=msg.get("timestamp"),
                chat=chat_data,
                feature_overview=feature_overview,
                tickets=tickets
            ))
    
    session = SessionDataWithConversation(
        session_id=session_data["session_id"],
        title=session_data["title"],
        created_at=session_data["created_at"],
        updated_at=session_data["updated_at"],
        conversation=conversation_messages
    )
    
    return SessionWithConversationResponse(
        data=[session],
        error=None
    )

@router.post("/process_feature", response_model=AgentOutput)
async def process_feature(input: FeatureInput):
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
                suggestions=None,
                progress=ChatProgress(
                    answered_questions=0,
                    total_questions=len(result.data.questions)
                )
            )
            
            # Parse markdown to extract feature overview and tickets
            markdown_sections = parse_markdown_sections(result.data.markdown)
            
            # Create feature overview from parsed data
            feature_overview = FeatureOverview(
                description=markdown_sections.get("description", "Feature description will be implemented in future iterations"),
                acceptance_criteria=markdown_sections.get("acceptance_criteria", []),
                progress_percentage=0  # Will be calculated in future iterations
            )
            
            # Create backend tickets from parsed data
            backend_tickets = []
            for backend_change in markdown_sections.get("backend_changes", []):
                backend_tickets.append(Ticket(
                    title=backend_change[:50] + "..." if len(backend_change) > 50 else backend_change,
                    description=backend_change,
                    technical_details=None,  # Will be implemented in future iterations
                    acceptance_criteria=None,  # Will be implemented in future iterations
                    cursor_prompt=None  # Will be implemented in future iterations
                ))
            
            # Create frontend tickets from parsed data
            frontend_tickets = []
            for frontend_change in markdown_sections.get("frontend_changes", []):
                frontend_tickets.append(Ticket(
                    title=frontend_change[:50] + "..." if len(frontend_change) > 50 else frontend_change,
                    description=frontend_change,
                    technical_details=None,  # Will be implemented in future iterations
                    acceptance_criteria=None,  # Will be implemented in future iterations
                    cursor_prompt=None  # Will be implemented in future iterations
                ))
            
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
            # Determine status code based on error type
            status_code = 500  # default
            if result.error.type == "security_rejection":
                status_code = 400
            elif result.error.type == "internal_server_error":
                status_code = 503
            
            return JSONResponse(
                status_code=status_code,
                content=AgentOutput(
                    data=None,
                    error=AgentOutputError(
                        type=result.error.type,
                        message=result.error.message
                    )
                ).model_dump()
            )
        
    except Exception as e:
        # This should rarely happen since AgentService now handles errors internally
        return JSONResponse(
            status_code=503,
            content=AgentOutput(
                data=None,
                error=AgentOutputError(
                    type="internal_server_error",
                    message=str(e)
                )
            ).model_dump()
        )

@router.delete("/clear_session/{session_id}", response_model=ClearSessionResponse)
async def clear_session(session_id: str):
    if session_service.clear_session(session_id):
        return ClearSessionResponse(
            data=ClearSessionData(
                message=f"Session {session_id} deleted"
            ),
            error=None
        )
    
    return JSONResponse(
        status_code=404,
        content=ClearSessionResponse(
            data=None,
            error=AgentOutputError(
                type="not_found",
                message="Session not found"
            )
        ).model_dump()
    ) 