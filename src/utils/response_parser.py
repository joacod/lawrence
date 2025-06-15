import re
from typing import Dict

def parse_response_to_json(text: str) -> Dict[str, str]:
    """
    Parse a text response containing RESPONSE and MARKDOWN sections into a JSON structure.
    
    Args:
        text (str): The input text containing RESPONSE and MARKDOWN sections
        
    Returns:
        Dict[str, str]: A dictionary with 'response' and 'markdown' keys
        
    Example:
        Input:
        RESPONSE:
        Hello, this is a response
        
        MARKDOWN:
        # Title
        Some markdown content
        
        Output:
        {
            "response": "Hello, this is a response",
            "markdown": "# Title\nSome markdown content"
        }
    """
    # Split the text into sections
    sections = re.split(r'(?:^|\n)(?:RESPONSE:|MARKDOWN:)', text)
    
    # Remove empty strings and strip whitespace
    sections = [s.strip() for s in sections if s.strip()]
    
    # If we don't have exactly two sections, raise an error
    if len(sections) != 2:
        raise ValueError("Input text must contain exactly two sections: RESPONSE and MARKDOWN")
    
    # Create the JSON structure
    return {
        "response": sections[0].strip(),
        "markdown": sections[1].strip()
    } 