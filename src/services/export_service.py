"""
Export Service
Handles business logic for exporting feature data to various formats.
"""
import base64
from typing import Optional, Tuple
from src.core.session_manager import SessionManager
from src.models.core_models import (
    ExportData, AgentError, FeatureOverview, TicketsData, Ticket
)
from src.utils.export_generator import (
    generate_markdown_export, generate_pdf_export, get_export_filename
)
from src.utils.parsers.markdown_parser import parse_markdown_sections
from src.utils.api.response_helpers import create_tickets_from_changes
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ExportService:
    """Service for handling feature export operations"""
    
    def __init__(self):
        self.session_manager = SessionManager()
    
    async def export_feature(self, session_id: str, export_format: str) -> Tuple[Optional[ExportData], Optional[AgentError]]:
        """
        Export feature data for a given session in the specified format.
        
        Args:
            session_id: The session identifier
            export_format: Export format ("markdown" or "pdf")
        
        Returns:
            Tuple containing either ExportData or AgentError
        """
        try:
            # Validate session exists
            if not self.session_manager.session_exists(session_id):
                logger.warning(f"Export requested for non-existent session: {session_id}")
                return None, AgentError(
                    type="not_found",
                    message=f"Session {session_id} not found"
                )
            
            # Get the latest session data with conversation
            session_data = self.session_manager.get_session_with_conversation(session_id)
            if not session_data:
                logger.error(f"Failed to retrieve session data for: {session_id}")
                return None, AgentError(
                    type="internal_server_error",
                    message="Failed to retrieve session data"
                )
            
            # Extract the most recent feature overview and tickets from conversation
            feature_overview, tickets = self._extract_latest_feature_data(session_data)
            
            if not feature_overview:
                logger.warning(f"No feature overview found in session: {session_id}")
                return None, AgentError(
                    type="not_found",
                    message="No feature overview found in this session"
                )
            
            # Generate export content
            title = session_data.get("title", "Untitled Feature")
            created_at = session_data.get("created_at")
            updated_at = session_data.get("updated_at")
            
            # Generate filename
            filename = get_export_filename(title, export_format, session_id)
            
            if export_format == "pdf":
                content = generate_pdf_export(
                    session_id=session_id,
                    title=title,
                    feature_overview=feature_overview,
                    tickets=tickets,
                    created_at=created_at,
                    updated_at=updated_at
                )
                # Encode PDF content as base64 for JSON response
                content_str = base64.b64encode(content).decode('utf-8')
                content_type = "application/pdf"
            else:
                content_str = generate_markdown_export(
                    session_id=session_id,
                    title=title,
                    feature_overview=feature_overview,
                    tickets=tickets,
                    created_at=created_at,
                    updated_at=updated_at
                )
                content_type = "text/markdown"
            
            export_data = ExportData(
                content=content_str,
                filename=filename,
                content_type=content_type
            )
            
            logger.info(f"Successfully exported {export_format} for session {session_id}")
            return export_data, None
            
        except Exception as e:
            logger.error(f"Error exporting session {session_id}: {str(e)}", exc_info=True)
            return None, AgentError(
                type="internal_server_error",
                message="An error occurred while generating the export"
            )
    
    def _extract_latest_feature_data(self, session_data: dict) -> Tuple[Optional[FeatureOverview], Optional[TicketsData]]:
        """
        Extract the most recent feature overview and tickets from session conversation.
        
        Args:
            session_data: Complete session data including conversation
        
        Returns:
            Tuple of FeatureOverview and TicketsData objects
        """
        try:
            conversation = session_data.get("conversation", [])
            
            # Look for the most recent assistant message with feature data
            latest_feature_overview = None
            latest_tickets = None
            latest_markdown = None
            
            # Process conversation in reverse order to get the most recent data
            for message in reversed(conversation):
                if message.get("type") == "assistant":
                    # Check if message has markdown content to parse
                    markdown = message.get("markdown", "")
                    if markdown and not latest_markdown:
                        latest_markdown = markdown
                        break
            
            if latest_markdown:
                # Parse markdown to extract feature overview and tickets
                markdown_sections = parse_markdown_sections(latest_markdown)
                
                # Create feature overview
                questions = session_data.get("questions", [])
                answered_questions = len([q for q in questions if q.get("status") == "answered"])
                total_questions = len(questions)
                progress_percentage = int((answered_questions / total_questions * 100) if total_questions > 0 else 0)
                
                latest_feature_overview = FeatureOverview(
                    description=markdown_sections.get("description", "Feature description will be available after processing"),
                    acceptance_criteria=markdown_sections.get("acceptance_criteria", []),
                    progress_percentage=progress_percentage
                )
                
                # Create tickets
                backend_tickets = create_tickets_from_changes(markdown_sections.get("backend_changes", []))
                frontend_tickets = create_tickets_from_changes(markdown_sections.get("frontend_changes", []))
                
                latest_tickets = TicketsData(
                    backend=backend_tickets,
                    frontend=frontend_tickets
                )
            
            # If no markdown found, create minimal feature overview
            if not latest_feature_overview:
                questions = session_data.get("questions", [])
                answered_questions = len([q for q in questions if q.get("status") == "answered"])
                total_questions = len(questions)
                progress_percentage = int((answered_questions / total_questions * 100) if total_questions > 0 else 0)
                
                latest_feature_overview = FeatureOverview(
                    description="Feature is still being processed. Please check back after providing more details.",
                    acceptance_criteria=[],
                    progress_percentage=progress_percentage
                )
                
                latest_tickets = TicketsData(backend=[], frontend=[])
            
            return latest_feature_overview, latest_tickets
            
        except Exception as e:
            logger.error(f"Error extracting feature data: {str(e)}", exc_info=True)
            return None, None 