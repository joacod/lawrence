"""
Tests for QuestionMatcher utility.
"""
import pytest
from src.utils.question_matcher import QuestionMatcher


class TestQuestionMatcher:
    """Test cases for QuestionMatcher."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.matcher = QuestionMatcher()
    
    def test_find_matching_password_complexity_question(self):
        """Test matching password complexity questions."""
        pending_questions = [
            {"question": "Do you envision any specific password complexity rules?"}
        ]
        
        user_input = "More than 8 characters with uppercase and numbers"
        matching_question = self.matcher.find_matching_question(user_input, pending_questions)
        
        assert matching_question is not None
        assert "password" in matching_question["question"].lower()
    
    def test_find_matching_security_measures_question(self):
        """Test matching security measures questions."""
        pending_questions = [
            {"question": "Will there be any additional authentication factors required?"}
        ]
        
        user_input = "Wait 1 hour after 5 failed attempts"
        matching_question = self.matcher.find_matching_question(user_input, pending_questions)
        
        assert matching_question is not None
        assert "authentication" in matching_question["question"].lower()
    
    def test_find_matching_registration_question(self):
        """Test matching registration questions."""
        pending_questions = [
            {"question": "Can users register with their email address?"}
        ]
        
        user_input = "Yes, users can register with email"
        matching_question = self.matcher.find_matching_question(user_input, pending_questions)
        
        assert matching_question is not None
        assert "register" in matching_question["question"].lower()
    
    def test_find_matching_password_reset_question(self):
        """Test matching password reset questions."""
        pending_questions = [
            {"question": "How should password reset be handled?"}
        ]
        
        user_input = "Send reset email with temporary link"
        matching_question = self.matcher.find_matching_question(user_input, pending_questions)
        
        assert matching_question is not None
        assert "reset" in matching_question["question"].lower()
    
    def test_no_matching_question(self):
        """Test when no question matches the user input."""
        pending_questions = [
            {"question": "What password complexity do you need?"}
        ]
        
        user_input = "I want to add a dashboard feature"
        matching_question = self.matcher.find_matching_question(user_input, pending_questions)
        
        assert matching_question is None
    
    def test_multiple_questions_find_correct_match(self):
        """Test matching with multiple questions present."""
        pending_questions = [
            {"question": "What password complexity do you need?"},
            {"question": "Will there be additional authentication factors?"},
            {"question": "Can users register with email?"}
        ]
        
        user_input = "Uppercase, lowercase, numbers, and special characters"
        matching_question = self.matcher.find_matching_question(user_input, pending_questions)
        
        assert matching_question is not None
        assert "password" in matching_question["question"].lower()
    
    def test_empty_pending_questions(self):
        """Test with empty pending questions list."""
        user_input = "Some user input"
        matching_question = self.matcher.find_matching_question(user_input, [])
        
        assert matching_question is None
    
    def test_question_patterns_property(self):
        """Test that question patterns are properly defined."""
        assert len(self.matcher.question_patterns) > 0
        
        for category, patterns in self.matcher.question_patterns.items():
            assert "question_keywords" in patterns
            assert "answer_keywords" in patterns
            assert len(patterns["question_keywords"]) > 0
            assert len(patterns["answer_keywords"]) > 0 