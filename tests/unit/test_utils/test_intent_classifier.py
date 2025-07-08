"""
Tests for IntentClassifier utility.
"""
import pytest
from src.utils.intent_classifier import IntentClassifier


class TestIntentClassifier:
    """Test cases for IntentClassifier."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = IntentClassifier()
    
    def test_classify_new_feature_intent(self):
        """Test classification of new feature intent."""
        # Test new feature indicators
        test_cases = [
            "I want to create a login system",
            "I need to build a dashboard",
            "Create a user management feature",
            "Implement a payment system",
            "Add a reporting module",
            "Build an e-commerce application"
        ]
        
        for user_input in test_cases:
            intent = self.classifier.classify_intent(user_input, [])
            assert intent == "new_feature", f"Expected 'new_feature' for: {user_input}"
    
    def test_classify_question_answer_intent(self):
        """Test classification of question answer intent."""
        existing_questions = [{"question": "What password complexity do you need?"}]
        
        # Test answer indicators
        test_cases = [
            "More than 8 characters with uppercase and numbers",
            "At least 10 characters minimum",
            "Yes, we need 2FA",
            "No additional authentication required",
            "Just email and password, nothing else",
            "Wait 1 hour after 5 failed attempts"
        ]
        
        for user_input in test_cases:
            intent = self.classifier.classify_intent(user_input, existing_questions)
            assert intent == "question_answer", f"Expected 'question_answer' for: {user_input}"
    
    def test_classify_with_no_existing_questions(self):
        """Test classification when no existing questions."""
        # Should default to new_feature when no questions exist
        intent = self.classifier.classify_intent("Some random input", [])
        assert intent == "new_feature"
    
    def test_classify_with_existing_questions_but_no_indicators(self):
        """Test classification with existing questions but no clear indicators."""
        existing_questions = [{"question": "What password complexity do you need?"}]
        
        # Input without clear indicators should default to question_answer
        intent = self.classifier.classify_intent("I think we should consider security", existing_questions)
        assert intent == "question_answer"
    
    def test_answer_indicators_property(self):
        """Test that answer indicators are properly defined."""
        assert len(self.classifier.answer_indicators) > 0
        assert all(isinstance(indicator, str) for indicator in self.classifier.answer_indicators)
    
    def test_new_feature_indicators_property(self):
        """Test that new feature indicators are properly defined."""
        assert len(self.classifier.new_feature_indicators) > 0
        assert all(isinstance(indicator, str) for indicator in self.classifier.new_feature_indicators) 