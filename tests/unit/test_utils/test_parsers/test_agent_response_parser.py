import pytest
from src.utils.parsers.agent_response_parser import parse_response_to_json


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