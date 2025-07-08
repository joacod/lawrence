"""
Intent Classifier Utility
Classifies user intent for feature requests and follow-ups.
"""
from typing import List, Dict


class IntentClassifier:
    """
    Classifies user intent to determine if input is a new feature or follow-up.
    """
    
    def __init__(self):
        """Initialize the intent classifier with keyword patterns."""
        self.answer_indicators = [
            'more than', 'at least', 'minimum', 'maximum', 'between',
            'yes', 'no', 'not', 'never', 'always', 'only', 'just',
            'characters', 'uppercase', 'lowercase', 'numbers', 'special',
            'attempts', 'wait', 'hour', 'minutes', 'seconds',
            'email', 'password', 'username', 'login', 'register'
        ]
        
        self.new_feature_indicators = [
            'i want', 'i need', 'create', 'build', 'implement', 'add',
            'feature', 'system', 'application', 'website', 'app'
        ]
    
    def classify_intent(self, user_input: str, existing_questions: List[dict]) -> str:
        """
        Classify user intent to determine if this is a new feature or follow-up.
        
        Args:
            user_input (str): The user's input
            existing_questions (List[dict]): Existing questions in the session
            
        Returns:
            str: 'new_feature', 'question_answer', or 'clarification'
        """
        input_lower = user_input.lower()
        
        # Check if input looks like an answer to a specific question
        if existing_questions:
            # If input contains specific answer patterns and there are pending questions
            if any(indicator in input_lower for indicator in self.answer_indicators):
                return 'question_answer'
        
        # Check if input looks like a new feature description
        if any(indicator in input_lower for indicator in self.new_feature_indicators):
            return 'new_feature'
        
        # Default to question answer if there are existing questions
        return 'question_answer' if existing_questions else 'new_feature' 