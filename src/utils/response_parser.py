import re
from typing import Dict, List, Union

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
            # Split by bullet points and clean up
            questions = []
            for line in questions_text.split('\n'):
                # Remove both * and - bullet points and clean up whitespace
                line = line.strip()
                if line.startswith('- '):
                    line = line[2:].strip()
                elif line.startswith('* '):
                    line = line[2:].strip()
                if line:
                    questions.append(line)
            return questions
    
    # If no PENDING QUESTIONS section or no questions found, try to extract from response
    response_match = re.search(r'RESPONSE:\n(.*?)(?=\n\n(?:PENDING QUESTIONS:|MARKDOWN:))', text, re.DOTALL)
    if response_match:
        response_text = response_match.group(1).strip()
        return extract_questions_from_response(response_text)
    
    return []

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
    
    # Split the text into sections
    sections = re.split(r'(?:^|\n)\s*(?:RESPONSE:|MARKDOWN:)', text)
    
    # Remove empty strings and strip whitespace
    sections = [s.strip() for s in sections if s.strip()]
    
    # If we don't have exactly two sections, raise an error
    if len(sections) != 2:
        raise ValueError("Input text must contain exactly two sections: RESPONSE and MARKDOWN")
    
    # Get response (remove PENDING QUESTIONS section if present)
    response = re.split(r'\nPENDING QUESTIONS:', sections[0])[0].strip()
    
    # Clean up response: remove "RESPONSE:" prefix if present
    response = re.sub(r'^RESPONSE:\s*', '', response).strip()
    
    markdown = sections[1].strip()
    
    # Create the JSON structure
    return {
        "response": response,
        "markdown": markdown,
        "questions": questions
    } 