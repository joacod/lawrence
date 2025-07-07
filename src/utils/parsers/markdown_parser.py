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

def _parse_changes_with_titles(changes_text: str) -> List[Dict[str, str]]:
    """
    Parse changes section to extract titles and descriptions.
    
    Args:
        changes_text (str): The text from a changes section
        
    Returns:
        List[Dict[str, str]]: List of dictionaries with 'title' and 'description' keys
    """
    changes = []
    for line in changes_text.split('\n'):
        line = _clean_bullet_point(line)
        if not line or line.startswith('##'):
            continue
            
        # Parse tickets format: **Title: [title]** - [description]
        title_match = re.search(r'\*\*Title:\s*([^*]+)\*\*\s*-\s*(.+)', line)
        if title_match:
            title = title_match.group(1).strip()
            description = title_match.group(2).strip()
            changes.append({
                "title": title,
                "description": description
            })
    
    return changes

def parse_markdown_sections(markdown_text: str) -> Dict[str, Union[str, List[str], List[Dict[str, str]]]]:
    """
    Parse markdown text to extract Description, Acceptance Criteria, Backend Changes, and Frontend Changes.
    
    Args:
        markdown_text (str): The markdown text to parse
        
    Returns:
        Dict[str, Union[str, List[str], List[Dict[str, str]]]]: A dictionary with 'description', 'acceptance_criteria', 
        'backend_changes', and 'frontend_changes' keys. Dictionaries with 'title' and 'description' keys.
        
    Example:
        Input:
        # Feature: Email/Password Login System
        
        ## Description
        A login system that allows users to access their account...
        
        ## Acceptance Criteria
        - Users are able to enter their email addresses and passwords
        - The system verifies the entered email and password...
        
        ## Backend Changes
        - **Title: Implement User Authentication** - Create authentication service with JWT tokens
        - **Title: Add Password Hashing** - Implement bcrypt password hashing for security
        
        ## Frontend Changes
        - **Title: Create Login Form** - Design responsive login form with validation
        - **Title: Add Error Handling** - Implement user-friendly error messages
        
        Output:
        {
            "description": "A login system that allows users to access their account...",
            "acceptance_criteria": [
                "Users are able to enter their email addresses and passwords",
                "The system verifies the entered email and password..."
            ],
            "backend_changes": [
                {"title": "Implement User Authentication", "description": "Create authentication service with JWT tokens"},
                {"title": "Add Password Hashing", "description": "Implement bcrypt password hashing for security"}
            ],
            "frontend_changes": [
                {"title": "Create Login Form", "description": "Design responsive login form with validation"},
                {"title": "Add Error Handling", "description": "Implement user-friendly error messages"}
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
    
    # Extract Backend Changes section with title parsing
    backend_match = re.search(r'## Backend Changes\n(.*?)(?=\n\n## )', markdown_text, re.DOTALL)
    if backend_match:
        backend_text = backend_match.group(1).strip()
        result["backend_changes"] = _parse_changes_with_titles(backend_text)
    
    # Extract Frontend Changes section with title parsing
    frontend_match = re.search(r'## Frontend Changes\n(.*?)(?=\n\n## |$)', markdown_text, re.DOTALL)
    if frontend_match:
        frontend_text = frontend_match.group(1).strip()
        result["frontend_changes"] = _parse_changes_with_titles(frontend_text)
    
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