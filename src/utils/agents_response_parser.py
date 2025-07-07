"""
Agent Response Parser
Handles parsing of different markdown sections from agent responses
based on the expected format for each agent type.
"""
import re
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod


class AgentResponseParser(ABC):
    """Abstract base class for agent response parsers."""
    
    @abstractmethod
    def parse(self, response_content: str) -> Dict[str, Any]:
        """Parse response content and return structured data."""
        pass
    
    def _extract_section(self, text: str, section_name: str) -> Optional[str]:
        """Extract a specific section from markdown text."""
        pattern = rf'{section_name}:\s*\n(.*?)(?=\n\w+:|$)'
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else None
    
    def _parse_key_value_section(self, section_content: str) -> Dict[str, str]:
        """Parse a key:value section into a dictionary."""
        result = {}
        for line in section_content.splitlines():
            # Handle both colon and semicolon separators
            if ':' in line:
                # Split on first colon only to handle values that might contain colons
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    # Remove trailing semicolons if present
                    value = value.rstrip(';')
                    result[key] = value
        return result


class SecurityAgentResponseParser(AgentResponseParser):
    """Parser for SecurityAgent responses (SECURITY section)."""
    
    def parse(self, response_content: str) -> Dict[str, Any]:
        """Parse security agent response."""
        security_section = self._extract_section(response_content, "SECURITY")
        if not security_section:
            raise ValueError("No SECURITY section found in response")
        
        key_values = self._parse_key_value_section(security_section)
        
        # Type conversions and validation
        is_feature_request = key_values.get('is_feature_request', '').lower() == 'true'
        try:
            confidence = float(key_values.get('confidence', 1.0))
        except ValueError:
            confidence = 1.0
        reasoning = key_values.get('reasoning', '')
        
        return {
            "is_feature_request": is_feature_request,
            "confidence": confidence,
            "reasoning": reasoning
        }


class ContextAgentResponseParser(AgentResponseParser):
    """Parser for ContextAgent responses (CONTEXT section)."""
    
    def parse(self, response_content: str) -> Dict[str, Any]:
        """Parse context agent response."""
        context_section = self._extract_section(response_content, "CONTEXT")
        if not context_section:
            raise ValueError("No CONTEXT section found in response")
        
        key_values = self._parse_key_value_section(context_section)
        
        is_contextually_relevant = key_values.get('is_contextually_relevant', '').lower() == 'true'
        reasoning = key_values.get('reasoning', '')
        
        return {
            "is_contextually_relevant": is_contextually_relevant,
            "reasoning": reasoning
        }


class QuestionAnalysisAgentResponseParser(AgentResponseParser):
    """Parser for QuestionAnalysisAgent responses (uses existing question parser)."""
    
    def parse(self, response_content: str) -> Dict[str, Any]:
        """Parse question analysis agent response."""
        # Use existing question parser from utils
        from src.utils.parsers.question_parser import parse_questions_section
        
        questions = parse_questions_section(response_content)
        return {
            "questions": questions
        }


class POAgentResponseParser(AgentResponseParser):
    """Parser for POAgent responses (RESPONSE/PENDING QUESTIONS/MARKDOWN sections)."""
    
    def parse(self, response_content: str) -> Dict[str, Any]:
        """Parse PO agent response."""
        # Use existing agent response parser from utils
        from src.utils.parsers.agent_response_parser import parse_response_to_json
        
        return parse_response_to_json(response_content)


class AgentResponseParserFactory:
    """Factory for creating appropriate agent response parsers."""
    
    _parsers = {
        "security": SecurityAgentResponseParser,
        "context": ContextAgentResponseParser,
        "question_analysis": QuestionAnalysisAgentResponseParser,
        "po": POAgentResponseParser
    }
    
    @classmethod
    def get_parser(cls, agent_type: str) -> AgentResponseParser:
        """Get the appropriate parser for an agent type."""
        if agent_type not in cls._parsers:
            raise ValueError(f"No parser available for agent type: {agent_type}")
        return cls._parsers[agent_type]()
    
    @classmethod
    def register_parser(cls, agent_type: str, parser_class: type) -> None:
        """Register a new parser for an agent type."""
        cls._parsers[agent_type] = parser_class 