"""
Agent Configuration System
Centralized configuration for all agents to eliminate hardcoded values
and provide consistent, maintainable agent settings.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from src.config.settings import settings


@dataclass
class AgentConfig:
    """Configuration for an individual agent."""
    model: str
    timeout: int
    temperature: float
    num_ctx: int
    retry_attempts: int = 2
    base_url: str = "http://localhost:11434"
    
    def to_llm_kwargs(self) -> Dict[str, Any]:
        """Convert to LLM initialization kwargs."""
        return {
            "model": self.model,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "temperature": self.temperature,
            "num_ctx": self.num_ctx
        }


class AgentConfigRegistry:
    """Registry of agent configurations."""
    
    _configs = {
        "security": AgentConfig(
            model=settings.SECURITY_MODEL,
            timeout=120,
            temperature=0.1,
            num_ctx=2048,
            retry_attempts=1  # Security doesn't need retries
        ),
        "context": AgentConfig(
            model=settings.CONTEXT_MODEL,
            timeout=120,
            temperature=0.1,
            num_ctx=2048,
            retry_attempts=1
        ),
        "question_analysis": AgentConfig(
            model=settings.QUESTION_ANALYSIS_MODEL,
            timeout=120,
            temperature=0.1,
            num_ctx=2048,
            retry_attempts=1
        ),
        "po": AgentConfig(
            model=settings.PO_MODEL,
            timeout=180,  # Longer timeout for complex responses
            temperature=0.7,  # Higher temperature for creativity
            num_ctx=4096,  # Larger context for conversation history
            retry_attempts=2  # POAgent needs retry logic
        )
    }
    
    @classmethod
    def get_config(cls, agent_type: str) -> AgentConfig:
        """Get configuration for an agent type."""
        if agent_type not in cls._configs:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return cls._configs[agent_type]
    
    @classmethod
    def register_config(cls, agent_type: str, config: AgentConfig) -> None:
        """Register a new agent configuration."""
        cls._configs[agent_type] = config
    
    @classmethod
    def list_agent_types(cls) -> list[str]:
        """Get list of registered agent types."""
        return list(cls._configs.keys()) 