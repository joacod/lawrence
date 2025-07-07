import uuid
from src.agents.security_agent import SecurityAgent
from src.agents.po_agent import POAgent
from src.core.session_manager import SessionManager
from src.models.core_models import AgentResponse, AgentSuccessData, AgentError
from src.utils.logger import setup_logger
from src.agents.context_agent import ContextAgent

logger = setup_logger(__name__)

class AgentService:
    def __init__(self):
        self.security_agent = SecurityAgent()
        self.po_agent = POAgent()
        self.session_manager = SessionManager()
        self.context_agent = ContextAgent()

    async def process_feature(self, feature: str, session_id: str | None = None) -> AgentResponse:
        """
        Main entry point for processing feature requests with coordinated agent evaluation.
        
        Coordinated Flow:
        1. ContextAgent: Determine if this is a follow-up to existing questions (if session exists)
        2. SecurityAgent: Evaluate with context-aware input (includes session context if available)
        3. POAgent: Process the feature, generate clarifications, etc.
        """
        session_id = session_id or str(uuid.uuid4())
        try:
            # Step 1: Context evaluation (if session exists)
            session_history = None
            context_result = None
            is_followup = False
            
            if session_id and self.session_manager.session_exists(session_id):
                session_history = self.session_manager.get_session_with_conversation(session_id)
                logger.info(f"Using session context: {self.session_manager.get_session_title(session_id)}")
                
                # Check if this is a follow-up to pending questions
                context_result = await self.context_agent.evaluate_context(
                    session_history=session_history,
                    user_followup=feature
                )
                is_followup = context_result.get("is_contextually_relevant", False)
                
                if is_followup:
                    logger.info("Context agent identified this as a follow-up to pending questions")
                else:
                    logger.info("Context agent determined this is not a follow-up to current session")

            # Step 2: Security evaluation with context awareness
            logger.info("Step 2: Security evaluation with context awareness")
            
            # Prepare context-aware input for security agent
            security_input = self._prepare_context_aware_security_input(
                feature=feature,
                session_history=session_history,
                is_followup=is_followup,
                context_result=context_result
            )
            
            security_result = await self.security_agent.evaluate_request(security_input)
            
            if not security_result.is_feature_request:
                logger.info("Request rejected by security agent")
                return AgentResponse(
                    error=AgentError(
                        type="security_rejection",
                        message=self._generate_security_rejection_message(security_result)
                    )
                )

            # Step 3: Additional context validation for non-followups
            if session_history and not is_followup:
                logger.info("Context agent rejected follow-up as not relevant to session context.")
                return AgentResponse(
                    error=AgentError(
                        type="context_deviation",
                        message="Your follow-up request does not appear to relate to the original feature. Please clarify your request or start a new feature."
                    )
                )

            # Step 4: PO agent processing
            logger.info("Step 3: PO agent processing")
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

    def _prepare_context_aware_security_input(self, feature: str, session_history: dict = None, 
                                            is_followup: bool = False, context_result: dict = None) -> str:
        """
        Prepare context-aware input for the security agent to prevent false rejections.
        
        This method creates a comprehensive input that includes:
        - The original user input
        - Session context if available
        - Context evaluation results
        - Clear indication if this is a follow-up response
        """
        if not session_history or not is_followup:
            # No session context or not a follow-up - use original input
            return feature
        
        # For follow-ups, provide context to help security agent understand this is valid
        context_info = []
        
        # Add context about pending questions
        if context_result and context_result.get("reasoning"):
            context_info.append(f"Context: {context_result['reasoning']}")
        
        # Add information about the current feature being worked on
        if session_history.get("title"):
            feature_title = session_history["title"]
            context_info.append(f"Current feature: {feature_title}")
        
        # Add pending questions for context - use the questions field directly
        pending_questions = []
        questions = session_history.get("questions", [])
        
        for q in questions:
            if q.get("status") == "pending":
                pending_questions.append(q["question"])
        
        if pending_questions:
            context_info.append("Pending questions:")
            for i, question in enumerate(pending_questions[:3], 1):  # Limit to 3 questions
                context_info.append(f"{i}. {question}")
        
        # Construct the context-aware input with clearer structure
        context_aware_input = f"""EVALUATE THIS REQUEST:

USER FOLLOW-UP RESPONSE: {feature}

CONTEXT INFORMATION:
- This is a follow-up response to pending questions about a software feature
- {' '.join(context_info)}

TASK: Determine if this follow-up response is related to software product management.
"""
        
        return context_aware_input.strip()

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