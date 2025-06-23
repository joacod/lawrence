import pytest
from src.utils.response_parser import (
    extract_questions_from_response,
    extract_questions,
    parse_markdown_sections,
    parse_response_to_json,
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


class TestExtractQuestions:
    """Test the extract_questions function."""
    
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
        
        result = extract_questions(text)
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
        
        result = extract_questions(text)
        assert len(result) == 2
        assert "What is the primary use case?" in result
        assert "Who are the target users?" in result
    
    def test_extract_questions_no_pending_section(self):
        """Test extracting questions from response when no PENDING QUESTIONS section."""
        text = """RESPONSE:
This is a response. What is the primary use case? Who are the target users?

MARKDOWN:
# Feature: Test"""
        
        result = extract_questions(text)
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
        
        result = extract_questions(text)
        assert len(result) == 1  # The response becomes a question
        assert "This is a response.?" in result  # Note the added question mark


class TestParseMarkdownSections:
    """Test the parse_markdown_sections function."""
    
    def test_parse_complete_markdown(self):
        """Test parsing complete markdown with all sections."""
        markdown = """# Feature: User Login System

## Description
A comprehensive user authentication system that allows users to register and login securely.

## Acceptance Criteria
- Users can register with email and password
- Users can login with valid credentials
- System validates input and provides feedback
- Password requirements are enforced

## Backend Changes
- Implement user authentication service
- Add JWT token generation
- Create password hashing utilities
- Add input validation middleware

## Frontend Changes
- Create registration form
- Create login form
- Add form validation
- Implement error handling"""
        
        result = parse_markdown_sections(markdown)
        
        assert result["description"] == "A comprehensive user authentication system that allows users to register and login securely."
        assert len(result["acceptance_criteria"]) == 4
        assert "Users can register with email and password" in result["acceptance_criteria"]
        assert len(result["backend_changes"]) == 4
        assert "Implement user authentication service" in result["backend_changes"]
        assert len(result["frontend_changes"]) == 4
        assert "Create registration form" in result["frontend_changes"]
    
    def test_parse_markdown_missing_sections(self):
        """Test parsing markdown with missing sections."""
        markdown = """# Feature: Simple Feature

## Description
A simple feature description.

## Acceptance Criteria
- Simple criteria"""
        
        result = parse_markdown_sections(markdown)
        
        assert result["description"] == "A simple feature description."
        assert len(result["acceptance_criteria"]) == 0  # No bullet points in the test data
        assert result["backend_changes"] == []
        assert result["frontend_changes"] == []
    
    def test_parse_markdown_empty(self):
        """Test parsing empty markdown."""
        result = parse_markdown_sections("")
        
        assert result["description"] == ""
        assert result["acceptance_criteria"] == []
        assert result["backend_changes"] == []
        assert result["frontend_changes"] == []
    
    def test_parse_markdown_different_bullet_styles(self):
        """Test parsing markdown with different bullet point styles."""
        markdown = """# Feature: Test Feature

## Description
Test description.

## Acceptance Criteria
- Dash bullet point
* Asterisk bullet point
- Another dash
* Another asterisk

## Backend Changes
- Backend change

## Frontend Changes
* Frontend change"""
        
        result = parse_markdown_sections(markdown)
        
        assert len(result["acceptance_criteria"]) == 4
        assert "Dash bullet point" in result["acceptance_criteria"]
        assert "Asterisk bullet point" in result["acceptance_criteria"]
        assert len(result["backend_changes"]) == 1
        assert len(result["frontend_changes"]) == 1


class TestParseResponseToJson:
    """Test the parse_response_to_json function."""
    
    def test_parse_complete_response(self):
        """Test parsing complete response with all sections."""
        text = """RESPONSE:
This is a test response for the feature.

PENDING QUESTIONS:
- What is the primary use case?
- Who are the target users?

MARKDOWN:
# Feature: Test Feature

## Description
This is a test feature description.

## Acceptance Criteria
- Users can perform the main action
- System validates input correctly

## Backend Changes
- Implement core logic
- Add validation

## Frontend Changes
- Create user interface
- Add form validation"""
        
        result = parse_response_to_json(text)
        
        assert result["response"] == "This is a test response for the feature."
        assert len(result["questions"]) == 2
        assert "What is the primary use case?" in result["questions"]
        assert "Who are the target users?" in result["questions"]
        assert "# Feature: Test Feature" in result["markdown"]
        assert "## Description" in result["markdown"]
    
    def test_parse_response_missing_questions_section(self):
        """Test parsing response without PENDING QUESTIONS section."""
        text = """RESPONSE:
This is a test response. What is the primary use case? Who are the target users?

MARKDOWN:
# Feature: Test Feature

## Description
Test description."""
        
        result = parse_response_to_json(text)
        
        assert result["response"] == "This is a test response. What is the primary use case? Who are the target users?"
        assert len(result["questions"]) == 2
        assert "# Feature: Test Feature" in result["markdown"]
    
    def test_parse_response_missing_response_section(self):
        """Test parsing response without RESPONSE section."""
        text = """PENDING QUESTIONS:
- Test question?

MARKDOWN:
# Feature: Test"""
        
        with pytest.raises(ValueError, match="Input text must contain a RESPONSE section"):
            parse_response_to_json(text)
    
    def test_parse_response_missing_markdown_section(self):
        """Test parsing response without MARKDOWN section."""
        text = """RESPONSE:
This is a test response.

PENDING QUESTIONS:
- Test question?"""
        
        with pytest.raises(ValueError, match="Input text must contain a MARKDOWN section"):
            parse_response_to_json(text) 