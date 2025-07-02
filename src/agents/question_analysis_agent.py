"""
Question Analysis Agent
Analyzes user responses against pending questions to update question status.
Uses the base agent framework with contextual input support.
"""
import json
from typing import List, Dict
from .base import ContextualAgent


class QuestionAnalysisAgent(ContextualAgent):
    """
    Question Analysis Agent analyzes user follow-ups against pending questions.
    
    Features:
    - Automatic configuration from AgentConfigRegistry
    - Built-in retry logic and error handling
    - Unified response parsing with question section support
    - Contextual input template for questions and user input
    """
    
    def __init__(self):
        """Initialize QuestionAnalysisAgent with 'question_analysis' configuration."""
        super().__init__(agent_type="question_analysis")
    
    def _get_contextual_template(self) -> str:
        """Get the contextual input template for pending questions and user follow-up."""
        return """PENDING QUESTIONS:
{pending_questions}

USER FOLLOW-UP:
{user_followup}"""
    
    async def analyze(self, pending_questions: List[Dict], user_followup: str) -> str:
        """
        Analyze user follow-up against pending questions to determine question status.
        
        Args:
            pending_questions (List[Dict]): List of pending questions with status
            user_followup (str): The user's follow-up input
            
        Returns:
            str: Raw markdown response content for compatibility with existing parsing
        """
        pending_questions_str = json.dumps(pending_questions, ensure_ascii=False)
        
        # Use the base agent's invoke method with automatic retry and parsing
        response_data = await self.invoke({
            "pending_questions": pending_questions_str,
            "user_followup": user_followup
        })
        
        # For compatibility with existing code that expects raw content,
        # we need to return the raw response. The base agent handles parsing internally.
        # Let's get the raw response instead of the parsed version.
        pending_questions_str = json.dumps(pending_questions, ensure_ascii=False)
        
        # Invoke directly to get raw content for compatibility
        result = await self.chain.ainvoke({
            "pending_questions": pending_questions_str,
            "user_followup": user_followup
        })
        
        return result.content
    
    async def process(self, pending_questions: List[Dict], user_followup: str) -> str:
        """Main processing method - delegates to analyze."""
        return await self.analyze(pending_questions, user_followup) 