from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from src.models.core_models import (
    FeatureInput, AgentOutput, AgentOutputData, AgentError as AgentOutputError, 
    HealthResponse, HealthData, SessionWithConversationResponse, 
    SessionDataWithConversation, ConversationMessage, ClearSessionResponse, ClearSessionData,
    ChatData, ChatProgress, FeatureOverview, TicketsData, Ticket
)
from src.services.agent_service import AgentService
from src.services.session_service import SessionService
from src.services.health_service import HealthService
from src.utils.response_parser import parse_markdown_sections

router = APIRouter()

# Dependency injection functions
def get_agent_service() -> AgentService:
    """Dependency to get agent service instance."""
    return AgentService()

def get_session_service() -> SessionService:
    """Dependency to get session service instance."""
    return SessionService()

def get_health_service() -> HealthService:
    """Dependency to get health service instance."""
    return HealthService()

def _create_tickets_from_changes(changes: list[str]) -> list[Ticket]:
    """Helper function to create tickets from a list of changes"""
    tickets = []
    for change in changes:
        tickets.append(Ticket(
            title=change[:50] + "..." if len(change) > 50 else change,
            description=change,
            technical_details=None,
            acceptance_criteria=None,
            cursor_prompt=None
        ))
    return tickets

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

@router.get("/session/{session_id}", response_model=SessionWithConversationResponse)
async def get_session(session_id: str, session_service: SessionService = Depends(get_session_service)):
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
            # Check if the message already has structured data (mocked sessions)
            if "chat" in msg and "feature_overview" in msg and "tickets" in msg:
                # Mocked session - use existing structured data
                conversation_messages.append(ConversationMessage(
                    type=msg["type"],
                    content=msg.get("content"),
                    timestamp=msg.get("timestamp"),
                    chat=msg["chat"],
                    feature_overview=msg["feature_overview"],
                    tickets=msg["tickets"]
                ))
            else:
                # Regular session - parse the markdown and create full structure
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
                backend_tickets = _create_tickets_from_changes(markdown_sections.get("backend_changes", []))
                
                # Create frontend tickets from parsed data
                frontend_tickets = _create_tickets_from_changes(markdown_sections.get("frontend_changes", []))
                
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
async def process_feature(
    input: FeatureInput, 
    agent_service: AgentService = Depends(get_agent_service)
):
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
                    answered_questions=getattr(result.data, 'answered_questions', 0),
                    total_questions=getattr(result.data, 'total_questions', len(result.data.questions))
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
            backend_tickets = _create_tickets_from_changes(markdown_sections.get("backend_changes", []))
            
            # Create frontend tickets from parsed data
            frontend_tickets = _create_tickets_from_changes(markdown_sections.get("frontend_changes", []))
            
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
            if result.error.type in ("security_rejection", "context_deviation"):
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
        # Handle unexpected exceptions
        return JSONResponse(
            status_code=503,
            content=AgentOutput(
                data=None,
                error=AgentOutputError(
                    type="internal_server_error",
                    message="An internal error occurred"
                )
            ).model_dump()
        )

@router.delete("/clear_session/{session_id}", response_model=ClearSessionResponse)
async def clear_session(session_id: str, session_service: SessionService = Depends(get_session_service)):
    """Clear a specific session by session_id"""
    success = session_service.clear_session(session_id)
    
    if not success:
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
    
    return ClearSessionResponse(
        data=ClearSessionData(message=f"Session {session_id} deleted"),
        error=None
    )

@router.get("/sessions")
async def list_sessions(session_service: SessionService = Depends(get_session_service)):
    """Get a list of all sessions with session_id and title."""
    sessions = session_service.list_sessions()
    return sessions 