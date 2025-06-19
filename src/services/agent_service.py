import logging
import sys
import uuid
from datetime import datetime, timezone
from src.services.security_agent import SecurityAgent
from src.services.po_agent import POAgent
from src.models.agent_response import AgentResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self):
        self.security_agent = SecurityAgent()
        self.po_agent = POAgent()

    async def process_feature(self, feature: str, session_id: str | None = None) -> AgentResponse:
        """
        Main entry point for processing feature requests.
        First evaluates with security agent, then processes with PO agent if approved.
        """
        session_id = session_id or str(uuid.uuid4())
        current_time = datetime.now(timezone.utc)
        
        try:
            # Step 1: Security evaluation
            logger.info("Step 1: Security evaluation")
            security_result = await self.security_agent.evaluate_request(feature)
            
            if not security_result.is_feature_request:
                logger.info("Request rejected by security agent")
                return AgentResponse(
                    success=False,
                    message=self._generate_security_rejection_message(security_result),
                    session_id=session_id,
                    created_at=current_time,
                    updated_at=current_time,
                    error_type="security_rejection"
                )
            
            logger.info("Request approved by security agent, proceeding to PO agent")
            
            # Step 2: PO agent processing
            logger.info("Step 2: PO agent processing")
            po_result = await self.po_agent.process_feature(feature, session_id)
            
            # Extract results from PO agent
            session_id, title, response, markdown, questions, created_at, updated_at = po_result
            
            return AgentResponse(
                success=True,
                message="Feature processed successfully",
                session_id=session_id,
                title=title,
                response=response,
                markdown=markdown,
                questions=questions,
                created_at=created_at,
                updated_at=updated_at
            )
            
        except Exception as e:
            logger.error("Error in agent service:", exc_info=True)
            return AgentResponse(
                success=False,
                message=f"An error occurred while processing your request: {str(e)}",
                session_id=session_id,
                created_at=current_time,
                updated_at=current_time,
                error_type="model_error"
            )

    def _generate_security_rejection_message(self, security_result) -> str:
        """Generate a user-friendly message for security rejections"""
        confidence = security_result.confidence
        reasoning = security_result.reasoning
        
        if confidence > 0.8:
            message = f"I apologize, but your request doesn't appear to be related to software product features. "
        elif confidence > 0.6:
            message = f"Your request seems to be outside the scope of software feature development. "
        else:
            message = f"I'm not sure if your request is related to software product features. "
        
        message += "This assistant is specifically designed to help with software feature development, documentation, and product management tasks. "
        message += "Please try asking about software features, user stories, acceptance criteria, or product requirements instead."
        
        if reasoning and len(reasoning.strip()) > 0:
            message += f"\n\nReasoning: {reasoning}"
        
        return message

    def clear_session(self, session_id: str) -> bool:
        """Clear a session from the PO agent"""
        return self.po_agent.clear_session(session_id) 