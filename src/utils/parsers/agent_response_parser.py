import re
from typing import Dict, List, Union
from src.utils.parsers.question_parser import extract_questions_from_text

def parse_response_to_json(text: str) -> Dict[str, Union[str, List[str]]]:
    """
    Parse a text response containing RESPONSE, optional PENDING QUESTIONS, and MARKDOWN sections into a JSON structure.
    If no explicit PENDING QUESTIONS section exists, extracts questions from the response text.
    
    Args:
        text (str): The input text containing all sections
        
    Returns:
        Dict[str, Union[str, List[str]]]: A dictionary with 'response', 'markdown', and 'questions' keys
        
    Example:
        Input:
        RESPONSE:
        Hello, this is a response

        PENDING QUESTIONS:
        * Question 1?
        * Question 2?
        * Question 3?

        MARKDOWN:
        # Title
        Some markdown content
        
        Output:
        {
            "response": "Hello, this is a response",
            "markdown": "# Title\nSome markdown content",
            "questions": ["Question 1?", "Question 2?", "Question 3?"]
        }
        
    Raises:
        ValueError: If required sections (RESPONSE, MARKDOWN) are missing
    """
    # Normalize the text by stripping leading/trailing whitespace and handling line endings
    text = text.strip()
    
    # Extract questions first (either from PENDING QUESTIONS or from response)
    questions = extract_questions_from_text(text)
    
    # Extract RESPONSE section
    response_match = re.search(r'RESPONSE:\s*(.*?)(?=PENDING QUESTIONS:|MARKDOWN:)', text, re.DOTALL)
    if not response_match:
        raise ValueError("Input text must contain a RESPONSE section")
    response = response_match.group(1).strip()
    
    # Extract MARKDOWN section
    markdown_match = re.search(r'MARKDOWN:\s*(.*?)$', text, re.DOTALL)
    if not markdown_match:
        raise ValueError("Input text must contain a MARKDOWN section")
    markdown = markdown_match.group(1).strip()
    
    # Create the JSON structure
    return {
        "response": response,
        "markdown": markdown,
        "questions": questions
    } 