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
    - Conversation history support for better context
    """
    
    def __init__(self):
        """Initialize QuestionAnalysisAgent with 'question_analysis' configuration."""
        super().__init__(agent_type="question_analysis")
    
    def _get_contextual_template(self) -> str:
        """Get the contextual input template for pending questions and user follow-up."""
        return """CONVERSATION CONTEXT:
{conversation_context}

PENDING QUESTIONS:
{pending_questions}

USER FOLLOW-UP:
{user_followup}

PREVIOUS QUESTIONS AND ANSWERS:
{previous_qa}"""
    
    async def analyze(self, pending_questions: List[Dict], user_followup: str, 
                     conversation_context: str = "", previous_qa: List[Dict] = None) -> str:
        """
        Analyze user follow-up against pending questions to determine question status.
        
        Args:
            pending_questions (List[Dict]): List of pending questions with status
            user_followup (str): The user's follow-up input
            conversation_context (str): Recent conversation history for context
            previous_qa (List[Dict]): Previously answered questions for context
            
        Returns:
            str: Raw markdown response content for compatibility with existing parsing
        """
        pending_questions_str = json.dumps(pending_questions, ensure_ascii=False)
        previous_qa_str = json.dumps(previous_qa or [], ensure_ascii=False)
        
        # Invoke directly to get raw content for compatibility
        result = await self.chain.ainvoke({
            "conversation_context": conversation_context,
            "pending_questions": pending_questions_str,
            "user_followup": user_followup,
            "previous_qa": previous_qa_str
        })
        
        return result.content
    
    async def process(self, pending_questions: List[Dict], user_followup: str, 
                     conversation_context: str = "", previous_qa: List[Dict] = None) -> str:
        """Main processing method - delegates to analyze."""
        return await self.analyze(pending_questions, user_followup, conversation_context, previous_qa) 