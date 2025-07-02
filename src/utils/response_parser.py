# This file serves as a facade for backward compatibility
# All parsing logic has been moved to specialized parsers

from typing import Dict, List, Union

# Import from specialized parsers
from src.utils.question_parser import (
    extract_questions_from_response,
    extract_questions_from_text as extract_questions,
    parse_questions_section
)

from src.utils.markdown_parser import (
    parse_markdown_sections,
    extract_title_from_markdown,
    parse_security_section,
    parse_context_section
)

from src.utils.agent_response_parser import (
    parse_response_to_json
)

# Re-export all functions for backward compatibility
__all__ = [
    'extract_questions_from_response',
    'extract_questions',
    'parse_markdown_sections',
    'parse_response_to_json',
    'parse_security_section',
    'parse_context_section',
    'parse_questions_section',
    'extract_title_from_markdown'
] 