import uuid
from src.agents.security_agent import SecurityAgent
from src.agents.po_agent import POAgent
from src.core.storage_manager import StorageManager
from src.models.core_models import AgentResponse, AgentSuccessData, AgentError
from src.utils.logger import setup_logger
from src.agents.context_agent import ContextAgent

logger = setup_logger(__name__)

class AgentService:
    def __init__(self):
        self.security_agent = SecurityAgent()
        self.po_agent = POAgent()
        self.storage = StorageManager()
        self.context_agent = ContextAgent()

    async def process_feature(self, feature: str, session_id: str | None = None) -> AgentResponse:
        """
        Main entry point for processing feature requests.
        1. SecurityAgent: Is this a valid software/product management request?
        2. ContextAgent: Is this request contextually relevant to the current session/feature/questions?
        3. POAgent: Process the feature, generate clarifications, etc.
        4. QuestionAnalysisAgent: Analyze user answers to pending questions.
        """
        session_id = session_id or str(uuid.uuid4())
        try:
            # Step 1: Security evaluation
            logger.info("Step 1: Security evaluation")
            security_result = await self.security_agent.evaluate_request(feature)
            if not security_result.is_feature_request:
                logger.info("Request rejected by security agent")
                return AgentResponse(
                    error=AgentError(
                        type="security_rejection",
                        message=self._generate_security_rejection_message(security_result)
                    )
                )

            # Step 2: Context evaluation (only if security passes)
            session_history = None
            if session_id and self.storage.session_exists(session_id):
                session_history = self.storage.get_all_session_data(session_id)
                logger.info(f"Using session context: {self.storage.get_session_title(session_id)}")
            if session_history:
                context_result = await self.context_agent.evaluate_context(
                    session_history=session_history,
                    user_followup=feature
                )
                if not context_result.get("is_contextually_relevant", False):
                    logger.info("Context agent rejected follow-up as not relevant to session context.")
                    return AgentResponse(
                        error=AgentError(
                            type="context_deviation",
                            message="Your follow-up request does not appear to relate to the original feature. Please clarify your request or start a new feature."
                        )
                    )

            # Step 3: PO agent processing
            logger.info("Step 2: PO agent processing")
            po_result = await self.po_agent.process_feature(feature, session_id)
            session_id, title, response, markdown, questions, total_questions, answered_questions, created_at, updated_at = po_result

            return AgentResponse(
                data=AgentSuccessData(
                    session_id=session_id,
                    title=title,
                    response=response,
                    markdown=markdown,
                    questions=questions,
                    created_at=created_at,
                    updated_at=updated_at,
                    answered_questions=answered_questions,
                    total_questions=total_questions
                )
            )
        except Exception as e:
            # Check if this is an Ollama connection error
            error_message = str(e).lower()
            if any(keyword in error_message for keyword in [
                "connection", "connect", "connection refused", "connection error", 
                "all connection attempts failed", "ollama"
            ]):
                logger.error("Ollama connection failed: %s", str(e))
                return AgentResponse(
                    error=AgentError(
                        type="internal_server_error",
                        message="An internal error occurred. Please try again later."
                    )
                )
            
            # For other errors, log the full traceback but keep user message generic
            logger.error("Error in agent service:", exc_info=True)
            return AgentResponse(
                error=AgentError(
                    type="internal_server_error",
                    message="An internal error occurred. Please try again later."
                )
            )

    def _generate_security_rejection_message(self, security_result) -> str:
        """Generate a user-friendly message for security rejections"""
        confidence = security_result.confidence
        reasoning = security_result.reasoning
        
        # Log the detailed reasoning for debugging
        logger.info(f"Security rejection - Confidence: {confidence}, Reasoning: {reasoning}")
        
        if confidence > 0.8:
            message = f"I apologize, but your request doesn't appear to be related to software product features. "
        elif confidence > 0.6:
            message = f"Your request seems to be outside the scope of software feature development. "
        else:
            message = f"I'm not sure if your request is related to software product features. "
        
        message += "This assistant is specifically designed to help with software feature development, documentation, and product management tasks. "
        message += "Please try asking about software features, user stories, acceptance criteria, or product requirements instead."
        
        return message 