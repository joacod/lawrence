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

def extract_title_from_markdown(markdown: str) -> str:
    """
    Extract title from markdown content by finding the first header.
    
    Args:
        markdown (str): The markdown content to parse
        
    Returns:
        str: The extracted title or "Untitled Feature" if no title found
    """
    markdown_lines = markdown.split('\n')
    for line in markdown_lines:
        line = line.strip()
        # Look for various markdown header formats
        if line.startswith('# Feature:'):
            return line.replace('# Feature:', '').strip()
        elif line.startswith('# '):
            # Extract title from any # header (most common case)
            return line.replace('# ', '').strip()
        elif line.startswith('## '):
            # If no # header found, try ## header
            return line.replace('## ', '').strip()
    
    # If no title found in markdown, use a default
    return "Untitled Feature"

def parse_security_section(markdown_text: str) -> Dict[str, Union[bool, float, str]]:
    """
    Parse SECURITY section from markdown block.
    
    Args:
        markdown_text (str): The markdown text containing a SECURITY section
        
    Returns:
        Dict[str, Union[bool, float, str]]: Security analysis result
        
    Raises:
        ValueError: If no SECURITY section is found
    """
    match = re.search(r'SECURITY:\s*\n(.*?)(?=\n\w+:|$)', markdown_text, re.DOTALL)
    if not match:
        raise ValueError("No SECURITY section found in response")
    
    section = match.group(1)
    result = {}
    for line in section.splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            result[key.strip()] = value.strip()
    
    is_feature_request = result.get('is_feature_request', '').lower() == 'true'
    try:
        confidence = float(result.get('confidence', 1.0))
    except Exception:
        confidence = 1.0
    reasoning = result.get('reasoning', '')
    
    return {
        "is_feature_request": is_feature_request,
        "confidence": confidence,
        "reasoning": reasoning
    }

def parse_context_section(markdown_text: str) -> Dict[str, Union[bool, str]]:
    """
    Parse CONTEXT section from markdown block.
    
    Args:
        markdown_text (str): The markdown text containing a CONTEXT section
        
    Returns:
        Dict[str, Union[bool, str]]: Context analysis result
        
    Raises:
        ValueError: If no CONTEXT section is found
    """
    match = re.search(r'CONTEXT:\s*\n(.*?)(?=\n\w+:|$)', markdown_text, re.DOTALL)
    if not match:
        raise ValueError("No CONTEXT section found in response")
    
    section = match.group(1)
    result = {}
    for line in section.splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            result[key.strip()] = value.strip()
    
    is_contextually_relevant = result.get('is_contextually_relevant', '').lower() == 'true'
    reasoning = result.get('reasoning', '')
    
    return {
        "is_contextually_relevant": is_contextually_relevant,
        "reasoning": reasoning
    } 