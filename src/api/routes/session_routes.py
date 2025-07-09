"""
Session management routes for handling conversation sessions.
"""
from fastapi import APIRouter, Depends
from src.models.core_models import (
    SessionWithConversationResponse, SessionDataWithConversation, 
    ConversationMessage, ClearSessionResponse, ClearSessionData,
    ChatData, ChatProgress, FeatureOverview, TicketsData
)
from src.services.session_service import SessionService
from src.api.dependencies import get_session_service
from src.utils.parsers.markdown_parser import parse_markdown_sections
from src.utils.api.error_handlers import create_not_found_response
from src.utils.api.response_helpers import create_tickets_from_changes

router = APIRouter(tags=["sessions"])


@router.get("/session/{session_id}", response_model=SessionWithConversationResponse)
async def get_session(session_id: str, session_service: SessionService = Depends(get_session_service)):
    """Get a specific session by session_id with full conversation history"""
    session_data = session_service.get_session_with_conversation(session_id)
    
    if not session_data:
        return create_not_found_response(
            response_model=SessionWithConversationResponse,
            resource_name="Session"
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
                backend_tickets = create_tickets_from_changes(markdown_sections.get("backend_changes", []))
                
                # Create frontend tickets from parsed data
                frontend_tickets = create_tickets_from_changes(markdown_sections.get("frontend_changes", []))
                
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


@router.delete("/clear_session/{session_id}", response_model=ClearSessionResponse)
async def clear_session(session_id: str, session_service: SessionService = Depends(get_session_service)):
    """Clear a specific session by session_id"""
    success = session_service.clear_session(session_id)
    
    if not success:
        return create_not_found_response(
            response_model=ClearSessionResponse,
            resource_name="Session"
        )
    
    return ClearSessionResponse(
        data=ClearSessionData(message=f"Session {session_id} deleted"),
        error=None
    )


@router.get("/sessions", response_model=list)
async def list_sessions(session_service: SessionService = Depends(get_session_service)):
    """Get a list of all sessions with session_id and title."""
    sessions = session_service.list_sessions()
    return sessions 