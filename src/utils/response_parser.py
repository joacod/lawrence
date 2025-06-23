import re
from typing import Dict, List, Union

def _clean_bullet_point(line: str) -> str:
    """Helper function to clean bullet points from a line"""
    line = line.strip()
    if line.startswith('- '):
        line = line[2:].strip()
    elif line.startswith('* '):
        line = line[2:].strip()
    elif line.startswith('-'):
        line = line[1:].strip()
    elif line.startswith('*'):
        line = line[1:].strip()
    return line

def extract_questions_from_response(response_text: str) -> List[str]:
    """
    Extract questions from the response text by looking for question marks.
    
    Args:
        response_text (str): The response text to analyze
        
    Returns:
        List[str]: List of questions found in the text
    """
    # Split by question marks and reconstruct questions
    potential_questions = [q.strip() + '?' for q in response_text.split('?') if q.strip()]
    
    # Filter out non-questions (should end with ? and be reasonably long)
    questions = [q for q in potential_questions if len(q) > 10 and '?' in q]
    
    return questions

def extract_questions(text: str) -> List[str]:
    """
    Extract questions from the PENDING QUESTIONS section or from the response if no section exists.
    
    Args:
        text (str): The full response text
        
    Returns:
        List[str]: List of questions, empty list if no questions found
    """
    # First try to find explicit PENDING QUESTIONS section
    match = re.search(r'PENDING QUESTIONS:\n(.*?)(?=\n\nMARKDOWN:)', text, re.DOTALL)
    if match:
        questions_text = match.group(1).strip()
        if questions_text:
            # Split by lines and clean up
            questions = []
            for line in questions_text.split('\n'):
                # Remove both * and - bullet points and clean up whitespace
                line = _clean_bullet_point(line)
                if line and not line.startswith('PENDING QUESTIONS:'):
                    questions.append(line)
            return questions
    
    # If no PENDING QUESTIONS section or no questions found, try to extract from response
    response_match = re.search(r'RESPONSE:\n(.*?)(?=\n\n(?:PENDING QUESTIONS:|MARKDOWN:))', text, re.DOTALL)
    if response_match:
        response_text = response_match.group(1).strip()
        return extract_questions_from_response(response_text)
    
    return []

def parse_markdown_sections(markdown_text: str) -> Dict[str, Union[str, List[str]]]:
    """
    Parse markdown text to extract Description, Acceptance Criteria, Backend Changes, and Frontend Changes.
    
    Args:
        markdown_text (str): The markdown text to parse
        
    Returns:
        Dict[str, Union[str, List[str]]]: A dictionary with 'description', 'acceptance_criteria', 
        'backend_changes', and 'frontend_changes' keys
        
    Example:
        Input:
        # Feature: Email/Password Login System
        
        ## Description
        A login system that allows users to access their account...
        
        ## Acceptance Criteria
        - Users are able to enter their email addresses and passwords
        - The system verifies the entered email and password...
        
        ## Backend Changes
        - Implement user authentication logic...
        
        ## Frontend Changes
        - Design and implement a login form...
        
        Output:
        {
            "description": "A login system that allows users to access their account...",
            "acceptance_criteria": [
                "Users are able to enter their email addresses and passwords",
                "The system verifies the entered email and password..."
            ],
            "backend_changes": [
                "Implement user authentication logic..."
            ],
            "frontend_changes": [
                "Design and implement a login form..."
            ]
        }
    """
    result = {
        "description": "",
        "acceptance_criteria": [],
        "backend_changes": [],
        "frontend_changes": []
    }
    
    # Extract Description section
    description_match = re.search(r'## Description\n(.*?)(?=\n\n## )', markdown_text, re.DOTALL)
    if description_match:
        result["description"] = description_match.group(1).strip()
    
    # Extract Acceptance Criteria section
    ac_match = re.search(r'## Acceptance Criteria\n(.*?)(?=\n\n## )', markdown_text, re.DOTALL)
    if ac_match:
        ac_text = ac_match.group(1).strip()
        # Split by lines and clean up bullet points
        for line in ac_text.split('\n'):
            line = _clean_bullet_point(line)
            if line and not line.startswith('##'):
                result["acceptance_criteria"].append(line)
    
    # Extract Backend Changes section
    backend_match = re.search(r'## Backend Changes\n(.*?)(?=\n\n## )', markdown_text, re.DOTALL)
    if backend_match:
        backend_text = backend_match.group(1).strip()
        # Split by lines and clean up bullet points
        for line in backend_text.split('\n'):
            line = _clean_bullet_point(line)
            if line and not line.startswith('##'):
                result["backend_changes"].append(line)
    
    # Extract Frontend Changes section
    frontend_match = re.search(r'## Frontend Changes\n(.*?)(?=\n\n## |$)', markdown_text, re.DOTALL)
    if frontend_match:
        frontend_text = frontend_match.group(1).strip()
        # Split by lines and clean up bullet points
        for line in frontend_text.split('\n'):
            line = _clean_bullet_point(line)
            if line and not line.startswith('##'):
                result["frontend_changes"].append(line)
    
    return result

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
    """
    # Extract questions first (either from PENDING QUESTIONS or from response)
    questions = extract_questions(text)
    
    # Extract RESPONSE section
    response_match = re.search(r'RESPONSE:\n(.*?)(?=\n\n(?:PENDING QUESTIONS:|MARKDOWN:))', text, re.DOTALL)
    if not response_match:
        raise ValueError("Input text must contain a RESPONSE section")
    response = response_match.group(1).strip()
    
    # Extract MARKDOWN section
    markdown_match = re.search(r'MARKDOWN:\n(.*?)$', text, re.DOTALL)
    if not markdown_match:
        raise ValueError("Input text must contain a MARKDOWN section")
    markdown = markdown_match.group(1).strip()
    
    # Create the JSON structure
    return {
        "response": response,
        "markdown": markdown,
        "questions": questions
    } 