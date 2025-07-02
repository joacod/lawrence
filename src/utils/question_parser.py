import re
from typing import List, Dict

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

def extract_questions_from_text(text: str) -> List[str]:
    """
    Extract questions from the PENDING QUESTIONS section or from the response if no section exists.
    
    Args:
        text (str): The full response text
        
    Returns:
        List[str]: List of questions, empty list if no questions found
    """
    # First try to find explicit PENDING QUESTIONS section
    match = re.search(r'PENDING QUESTIONS:\s*(.*?)(?=MARKDOWN:)', text, re.DOTALL)
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
    response_match = re.search(r'RESPONSE:\s*(.*?)(?=PENDING QUESTIONS:|MARKDOWN:)', text, re.DOTALL)
    if response_match:
        response_text = response_match.group(1).strip()
        return extract_questions_from_response(response_text)
    
    return []

def parse_questions_section(markdown_text: str) -> List[Dict]:
    """
    Parse QUESTIONS section from markdown block into a list of dicts.
    
    Args:
        markdown_text (str): The markdown text containing a QUESTIONS section
        
    Returns:
        List[Dict]: List of question dictionaries with question, status, and user_answer
        
    Raises:
        ValueError: If no QUESTIONS section is found
    """
    match = re.search(r'QUESTIONS:\s*\n(.*?)(?=\n\w+:|$)', markdown_text, re.DOTALL)
    if not match:
        raise ValueError("No QUESTIONS section found in response")
    
    section = match.group(1)
    questions = []
    current = {}
    
    for line in section.splitlines():
        line = line.strip()
        if line.startswith('- question:'):
            if current:
                questions.append(current)
            current = {"question": line[len('- question:'):].strip().strip('"')}
        elif line.startswith('status:'):
            current["status"] = line[len('status:'):].strip().strip('"')
        elif line.startswith('user_answer:'):
            val = line[len('user_answer:'):].strip()
            if val.lower() == 'null':
                current["user_answer"] = None
            else:
                current["user_answer"] = val.strip('"')
    
    if current:
        questions.append(current)
    
    return questions 