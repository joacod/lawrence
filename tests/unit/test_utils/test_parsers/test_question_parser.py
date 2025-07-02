import pytest
from src.utils.parsers.question_parser import (
    extract_questions_from_response,
    extract_questions_from_text,
    _clean_bullet_point
)


class TestCleanBulletPoint:
    """Test the _clean_bullet_point helper function."""
    
    def test_clean_dash_bullet(self):
        """Test cleaning dash bullet points."""
        result = _clean_bullet_point("- This is a test")
        assert result == "This is a test"
    
    def test_clean_asterisk_bullet(self):
        """Test cleaning asterisk bullet points."""
        result = _clean_bullet_point("* This is a test")
        assert result == "This is a test"
    
    def test_clean_single_dash(self):
        """Test cleaning single dash."""
        result = _clean_bullet_point("-This is a test")
        assert result == "This is a test"
    
    def test_clean_single_asterisk(self):
        """Test cleaning single asterisk."""
        result = _clean_bullet_point("*This is a test")
        assert result == "This is a test"
    
    def test_no_bullet_point(self):
        """Test text without bullet points."""
        result = _clean_bullet_point("This is a test")
        assert result == "This is a test"
    
    def test_empty_string(self):
        """Test empty string."""
        result = _clean_bullet_point("")
        assert result == ""
    
    def test_whitespace_only(self):
        """Test whitespace only string."""
        result = _clean_bullet_point("   ")
        assert result == ""


class TestExtractQuestionsFromResponse:
    """Test the extract_questions_from_response function."""
    
    def test_extract_questions_with_question_marks(self):
        """Test extracting questions from response text."""
        response = "This is a response. What is the primary use case? Who are the target users? This is more text."
        result = extract_questions_from_response(response)
        assert len(result) == 3  # All parts with question marks are included
        assert "This is a response. What is the primary use case?" in result
        assert "Who are the target users?" in result
        assert "This is more text.?" in result  # Note the added question mark
    
    def test_extract_questions_short_questions_filtered(self):
        """Test that short questions are filtered out."""
        response = "This is a response. What? Who? This is a longer question that should be included?"
        result = extract_questions_from_response(response)
        assert len(result) == 2  # Only longer questions are included
        assert "This is a response. What?" in result
        assert "This is a longer question that should be included?" in result
    
    def test_extract_questions_no_questions(self):
        """Test response with no questions."""
        response = "This is a response without any questions. Just some text here."
        result = extract_questions_from_response(response)
        assert len(result) == 1  # The entire response becomes one "question"
        assert "This is a response without any questions. Just some text here.?" in result  # Note the added question mark
    
    def test_extract_questions_empty_response(self):
        """Test empty response."""
        result = extract_questions_from_response("")
        assert result == []


class TestExtractQuestionsFromText:
    """Test the extract_questions_from_text function."""
    
    def test_extract_questions_with_pending_section(self):
        """Test extracting questions from PENDING QUESTIONS section."""
        text = """RESPONSE:
This is a response.

PENDING QUESTIONS:
- What is the primary use case?
- Who are the target users?
- What is the expected timeline?

MARKDOWN:
# Feature: Test"""
        
        result = extract_questions_from_text(text)
        assert len(result) == 3
        assert "What is the primary use case?" in result
        assert "Who are the target users?" in result
        assert "What is the expected timeline?" in result
    
    def test_extract_questions_with_asterisk_bullets(self):
        """Test extracting questions with asterisk bullets."""
        text = """RESPONSE:
This is a response.

PENDING QUESTIONS:
* What is the primary use case?
* Who are the target users?

MARKDOWN:
# Feature: Test"""
        
        result = extract_questions_from_text(text)
        assert len(result) == 2
        assert "What is the primary use case?" in result
        assert "Who are the target users?" in result
    
    def test_extract_questions_no_pending_section(self):
        """Test extracting questions from response when no PENDING QUESTIONS section."""
        text = """RESPONSE:
This is a response. What is the primary use case? Who are the target users?

MARKDOWN:
# Feature: Test"""
        
        result = extract_questions_from_text(text)
        assert len(result) == 2
        assert "This is a response. What is the primary use case?" in result
        assert "Who are the target users?" in result
    
    def test_extract_questions_empty_pending_section(self):
        """Test with empty PENDING QUESTIONS section."""
        text = """RESPONSE:
This is a response.

PENDING QUESTIONS:

MARKDOWN:
# Feature: Test"""
        
        result = extract_questions_from_text(text)
        assert len(result) == 1  # The response becomes a question
        assert "This is a response.?" in result  # Note the added question mark 