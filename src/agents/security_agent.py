"""
Security Agent
Evaluates if user requests are valid software product management requests.
Uses the base agent framework for consistent, maintainable code.
"""
from typing import Optional, Dict
from src.models.core_models import SecurityResponse
from .base import SimpleAgent


class SecurityAgent(SimpleAgent):
    """
    Security Agent evaluates if user input is a valid software product management request.
    
    Features:
    - Automatic configuration from AgentConfigRegistry
    - Built-in retry logic and error handling
    - Unified response parsing
    - Consistent logging
    """
    
    def __init__(self):
        """Initialize SecurityAgent with 'security' configuration."""
        super().__init__(agent_type="security")
    
    async def evaluate_request(self, user_input: str, session_context: Optional[Dict] = None) -> SecurityResponse:
        """
        Evaluate if the user input is a valid software product management related request.
        
        Args:
            user_input (str): The user's input text to evaluate
            session_context (Optional[Dict]): Context about the current session (ignored for security check)
            
        Returns:
            SecurityResponse: Object containing the evaluation results
        """
        # Use the base agent's invoke method with automatic retry and parsing
        response_data = await self.invoke({"input": user_input})
        
        # Convert parsed response to SecurityResponse model
        return SecurityResponse(
            is_feature_request=response_data["is_feature_request"],
            confidence=float(response_data["confidence"]),
            reasoning=response_data["reasoning"]
        )
    
    async def process(self, user_input: str, session_context: Optional[Dict] = None) -> SecurityResponse:
        """Main processing method - delegates to evaluate_request."""
        return await self.evaluate_request(user_input, session_context) 