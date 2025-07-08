"""
Question Deduplicator Utility
Detects and filters duplicate questions to avoid redundancy.
"""
from typing import List, Dict, Set


class QuestionDeduplicator:
    """
    Detects and filters duplicate questions using topic-based similarity.
    """
    
    def __init__(self):
        """Initialize the question deduplicator with similarity patterns."""
        self.similarity_keywords = {
            '2fa': ['two factor', 'two-factor', '2fa', 'authentication', 'additional authentication'],
            'password_reset': ['forgotten password', 'password reset', 'password recovery', 'reset password', 'forgot password'],
            'registration': ['register', 'registration', 'sign up', 'account creation', 'new account'],
            'password_complexity': [
                'password complexity', 'password rules', 'password requirements', 'minimum length', 
                'special characters', 'uppercase', 'lowercase', 'numbers', 'characters', 'password strength'
            ],
            'password_attempts': [
                'wrong password', 'incorrect password', 'failed attempts', 'attempts', 'wrong attempts',
                'lock account', 'lockout', 'brute force', 'wait', 'hour', 'minutes', 'block'
            ],
            'security': ['security measures', 'security', 'protection', 'lock', 'secure'],
            'email': ['email verification', 'email link', 'email code', 'email reset', 'email'],
            'user_management': ['user', 'account', 'profile', 'user type', 'role']
        }
    
    def is_similar_question(self, new_question: str, existing_questions: List[dict]) -> bool:
        """
        Check if a new question is similar to existing questions.
        
        Args:
            new_question (str): The new question to check
            existing_questions (List[dict]): List of existing questions
            
        Returns:
            bool: True if similar question exists, False otherwise
        """
        new_question_lower = new_question.lower()
        
        for category, keywords in self.similarity_keywords.items():
            # Check if new question contains any keywords from this category
            new_has_keywords = any(keyword in new_question_lower for keyword in keywords)
            
            if new_has_keywords:
                # Check if any existing question has similar keywords
                for existing_q in existing_questions:
                    existing_text = existing_q.get('question', '').lower()
                    existing_has_keywords = any(keyword in existing_text for keyword in keywords)
                    
                    if existing_has_keywords:
                        # Check if the existing question is already answered
                        if existing_q.get('status') == 'answered':
                            # If the existing question is answered and covers the same topic,
                            # the new question is redundant
                            if self._are_questions_about_same_topic(new_question_lower, existing_text):
                                return True
                        else:
                            # If the existing question is pending, check if they're asking the same thing
                            if self._are_questions_about_same_topic(new_question_lower, existing_text):
                                return True
        
        return False
    
    def _are_questions_about_same_topic(self, question1: str, question2: str) -> bool:
        """
        Check if two questions are about the same topic.
        
        Args:
            question1 (str): First question (lowercase)
            question2 (str): Second question (lowercase)
            
        Returns:
            bool: True if questions are about the same topic
        """
        topics1 = self._extract_topics(question1)
        topics2 = self._extract_topics(question2)
        
        # If they share any topic, they're about the same subject
        return bool(topics1 & topics2)
    
    def _extract_topics(self, question: str) -> Set[str]:
        """
        Extract key topic words from questions.
        
        Args:
            question (str): The question to analyze
            
        Returns:
            Set[str]: Set of detected topics
        """
        topics = set()
        
        # Authentication topics
        if any(word in question for word in ['2fa', 'two factor', 'authentication', 'additional authentication']):
            topics.add('2fa')
        
        # Password reset topics
        if any(word in question for word in ['password reset', 'forgotten password', 'forgot password', 'password recovery']):
            topics.add('password_reset')
        
        # Registration topics
        if any(word in question for word in ['register', 'registration', 'sign up', 'account creation']):
            topics.add('registration')
        
        # Password complexity topics
        if any(word in question for word in ['password complexity', 'password rules', 'password requirements', 'minimum length', 'special characters', 'uppercase', 'lowercase', 'numbers']):
            topics.add('password_complexity')
        
        # Password attempts/security topics
        if any(word in question for word in ['wrong password', 'incorrect password', 'failed attempts', 'attempts', 'lock account', 'lockout', 'brute force', 'wait', 'hour']):
            topics.add('password_attempts')
        
        # General security topics
        if 'security' in question:
            topics.add('security')
        
        # Email topics
        if 'email' in question:
            topics.add('email')
        
        # User management topics
        if any(word in question for word in ['user', 'account', 'profile', 'role']):
            topics.add('user_management')
        
        return topics
    
    def is_question_already_answered(self, question_text: str, existing_questions: List[dict]) -> bool:
        """
        Check if a question has already been answered by the user.
        
        Args:
            question_text (str): The question to check
            existing_questions (List[dict]): List of existing questions
            
        Returns:
            bool: True if the question has already been answered
        """
        question_lower = question_text.lower()
        
        # Check if any answered question covers the same topic
        for existing_q in existing_questions:
            if existing_q.get('status') == 'answered':
                existing_text = existing_q.get('question', '').lower()
                
                # If they're about the same topic and the existing one is answered
                if self._are_questions_about_same_topic(question_lower, existing_text):
                    return True
        
        return False
    
    def filter_duplicate_questions(self, new_questions: List, existing_questions: List[dict]) -> List:
        """
        Filter out questions that are similar to existing ones.
        
        Args:
            new_questions (List): List of new questions (strings or dicts)
            existing_questions (List[dict]): List of existing questions
            
        Returns:
            List: Filtered list of new questions without duplicates
        """
        filtered_questions = []
        
        for new_q in new_questions:
            if isinstance(new_q, str):
                question_text = new_q
            elif isinstance(new_q, dict):
                question_text = new_q.get('question', '')
            else:
                continue
            
            # Check if this question is similar to existing ones
            if not self.is_similar_question(question_text, existing_questions):
                # Additional check: ensure the question hasn't been answered in recent user input
                if not self.is_question_already_answered(question_text, existing_questions):
                    filtered_questions.append(new_q)
        
        return filtered_questions 