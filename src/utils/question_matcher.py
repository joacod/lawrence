"""
Question Matcher Utility
Matches user input to specific pending questions.
"""
from typing import List, Dict, Optional


class QuestionMatcher:
    """
    Matches user input to specific pending questions using keyword patterns.
    """
    
    def __init__(self):
        """Initialize the question matcher with keyword patterns."""
        self.question_patterns = {
            'password_complexity': {
                'question_keywords': ['password', 'complexity', 'rules', 'length', 'characters'],
                'answer_keywords': ['character', 'uppercase', 'lowercase', 'number', 'special', 'minimum', 'maximum']
            },
            'security_measures': {
                'question_keywords': ['security', 'two-factor', '2fa', 'captcha', 'authentication'],
                'answer_keywords': ['attempt', 'wait', 'hour', 'lock', 'block']
            },
            'registration': {
                'question_keywords': ['register', 'account', 'existing'],
                'answer_keywords': ['register', 'account', 'email']
            },
            'password_reset': {
                'question_keywords': ['forgotten', 'reset', 'recovery'],
                'answer_keywords': ['reset', 'forgot', 'recovery', 'email']
            }
        }
    
    def find_matching_question(self, user_input: str, pending_questions: List[dict]) -> Optional[dict]:
        """
        Find the most likely question the user is answering.
        
        Args:
            user_input (str): The user's input
            pending_questions (List[dict]): List of pending questions
            
        Returns:
            dict | None: The matching question or None
        """
        input_lower = user_input.lower()
        
        for question in pending_questions:
            question_text = question.get('question', '').lower()
            
            # Check each pattern category
            for category, patterns in self.question_patterns.items():
                question_has_keywords = any(
                    keyword in question_text 
                    for keyword in patterns['question_keywords']
                )
                input_has_keywords = any(
                    keyword in input_lower 
                    for keyword in patterns['answer_keywords']
                )
                
                if question_has_keywords and input_has_keywords:
                    return question
        
        return None 