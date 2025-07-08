"""
Tests for QuestionDeduplicator utility.
"""
import pytest
from src.utils.question_deduplicator import QuestionDeduplicator


class TestQuestionDeduplicator:
    """Test cases for QuestionDeduplicator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.deduplicator = QuestionDeduplicator()
    
    def test_is_similar_question_same_topic(self):
        """Test detecting similar questions about the same topic."""
        existing_questions = [
            {"question": "Do you need password complexity rules?", "status": "pending"}
        ]
        
        new_question = "What password requirements should we implement?"
        is_similar = self.deduplicator.is_similar_question(new_question, existing_questions)
        
        assert is_similar is True
    
    def test_is_similar_question_different_topic(self):
        """Test that different topics are not considered similar."""
        existing_questions = [
            {"question": "Do you need password complexity rules?", "status": "pending"}
        ]
        
        new_question = "What dashboard features do you want?"
        is_similar = self.deduplicator.is_similar_question(new_question, existing_questions)
        
        assert is_similar is False
    
    def test_is_similar_question_already_answered(self):
        """Test that questions about answered topics are considered similar."""
        existing_questions = [
            {"question": "Do you need password complexity rules?", "status": "answered"}
        ]
        
        new_question = "What password requirements should we implement?"
        is_similar = self.deduplicator.is_similar_question(new_question, existing_questions)
        
        assert is_similar is True
    
    def test_extract_topics_2fa(self):
        """Test extracting 2FA topics."""
        question = "Is two-factor authentication required?"
        topics = self.deduplicator._extract_topics(question)
        
        assert "2fa" in topics
    
    def test_extract_topics_password_reset(self):
        """Test extracting password reset topics."""
        question = "How should password reset be handled?"
        topics = self.deduplicator._extract_topics(question)
        
        assert "password_reset" in topics
    
    def test_extract_topics_registration(self):
        """Test extracting registration topics."""
        question = "Can users register with email?"
        topics = self.deduplicator._extract_topics(question)
        
        assert "registration" in topics
    
    def test_extract_topics_password_complexity(self):
        """Test extracting password complexity topics."""
        question = "What password complexity rules do you need?"
        topics = self.deduplicator._extract_topics(question)
        
        assert "password_complexity" in topics
    
    def test_extract_topics_multiple(self):
        """Test extracting multiple topics from one question."""
        question = "What security measures and password rules do you need?"
        topics = self.deduplicator._extract_topics(question)
        
        assert "security" in topics
        assert "password_complexity" in topics
    
    def test_are_questions_about_same_topic(self):
        """Test topic comparison between questions."""
        question1 = "Do you need password complexity rules?"
        question2 = "What password requirements should we implement?"
        
        same_topic = self.deduplicator._are_questions_about_same_topic(question1, question2)
        assert same_topic is True
    
    def test_are_questions_about_different_topics(self):
        """Test that different topics are not considered the same."""
        question1 = "Do you need password complexity rules?"
        question2 = "What dashboard features do you want?"
        
        same_topic = self.deduplicator._are_questions_about_same_topic(question1, question2)
        assert same_topic is False
    
    def test_is_question_already_answered(self):
        """Test detecting if a question has already been answered."""
        existing_questions = [
            {"question": "Do you need password complexity rules?", "status": "answered"}
        ]
        
        question_text = "What password requirements should we implement?"
        already_answered = self.deduplicator.is_question_already_answered(question_text, existing_questions)
        
        assert already_answered is True
    
    def test_is_question_not_already_answered(self):
        """Test that unanswered questions are not considered answered."""
        existing_questions = [
            {"question": "Do you need password complexity rules?", "status": "pending"}
        ]
        
        question_text = "What password requirements should we implement?"
        already_answered = self.deduplicator.is_question_already_answered(question_text, existing_questions)
        
        assert already_answered is False
    
    def test_filter_duplicate_questions_strings(self):
        """Test filtering duplicate questions from string list."""
        existing_questions = [
            {"question": "Do you need password complexity rules?", "status": "pending"}
        ]
        
        new_questions = [
            "What password requirements should we implement?",
            "What dashboard features do you want?",
            "Do you need 2FA?"
        ]
        
        filtered = self.deduplicator.filter_duplicate_questions(new_questions, existing_questions)
        
        # Should filter out the password complexity question
        assert len(filtered) == 2
        assert "dashboard" in filtered[0]
        assert "2FA" in filtered[1]
    
    def test_filter_duplicate_questions_dicts(self):
        """Test filtering duplicate questions from dict list."""
        existing_questions = [
            {"question": "Do you need password complexity rules?", "status": "pending"}
        ]
        
        new_questions = [
            {"question": "What password requirements should we implement?"},
            {"question": "What dashboard features do you want?"},
            {"question": "Do you need 2FA?"}
        ]
        
        filtered = self.deduplicator.filter_duplicate_questions(new_questions, existing_questions)
        
        # Should filter out the password complexity question
        assert len(filtered) == 2
        assert "dashboard" in filtered[0]["question"]
        assert "2FA" in filtered[1]["question"]
    
    def test_filter_duplicate_questions_mixed_types(self):
        """Test filtering with mixed question types."""
        existing_questions = [
            {"question": "Do you need password complexity rules?", "status": "pending"}
        ]
        
        new_questions = [
            "What password requirements should we implement?",
            {"question": "What dashboard features do you want?"},
            None,  # Should be skipped
            "Do you need 2FA?"
        ]
        
        filtered = self.deduplicator.filter_duplicate_questions(new_questions, existing_questions)
        
        # Should filter out the password complexity question and skip None
        assert len(filtered) == 2
        assert "dashboard" in filtered[0]["question"]
        assert "2FA" in filtered[1]
    
    def test_similarity_keywords_property(self):
        """Test that similarity keywords are properly defined."""
        assert len(self.deduplicator.similarity_keywords) > 0
        
        for category, keywords in self.deduplicator.similarity_keywords.items():
            assert len(keywords) > 0
            assert all(isinstance(keyword, str) for keyword in keywords) 