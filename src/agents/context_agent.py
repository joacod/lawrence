"""
Context Agent
Evaluates if follow-up requests are contextually relevant to the current session.
Uses the new base agent framework with contextual input support.
"""
from typing import Dict
from .base import ContextualAgent


class ContextAgent(ContextualAgent):
    """
    Context Agent evaluates if user follow-ups are contextually relevant to the session.
    
    Features:
    - Automatic configuration from AgentConfigRegistry
    - Built-in retry logic and error handling
    - Unified response parsing with CONTEXT section support
    - Contextual input template for pending questions
    """
    
    def __init__(self):
        """Initialize ContextAgent with 'context' configuration."""
        super().__init__(agent_type="context")
    
    def _get_contextual_template(self) -> str:
        """Get the contextual input template for pending questions and user follow-up."""
        return """PENDING QUESTIONS:
{pending_questions}

USER FOLLOW-UP:
{user_followup}"""
    
    def _format_pending_questions(self, session_history: dict) -> str:
        """Format pending questions from session history."""
        # Only show the most recent assistant's pending questions
        for msg in reversed(session_history.get("conversation", [])):
            if msg["type"] == "assistant" and msg.get("questions"):
                return "\n".join([
                    f"- {q['question']} (status: {q.get('status', 'pending')})" 
                    for q in msg["questions"]
                ])
        return ""
    
    async def evaluate_context(self, session_history: dict, user_followup: str) -> dict:
        """
        Evaluate if the user follow-up is contextually relevant to the session.
        
        Args:
            session_history (dict): The session conversation history
            user_followup (str): The user's follow-up input
            
        Returns:
            dict: Contains is_contextually_relevant (bool) and reasoning (str)
        """
        pending_questions_str = self._format_pending_questions(session_history)
        
        # Use the base agent's invoke method with automatic retry and parsing
        response_data = await self.invoke({
            "pending_questions": pending_questions_str,
            "user_followup": user_followup
        })
        
        return response_data
    
    async def process(self, session_history: dict, user_followup: str) -> dict:
        """Main processing method - delegates to evaluate_context."""
        return await self.evaluate_context(session_history, user_followup) 