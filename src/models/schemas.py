# This file serves as a facade for backward compatibility
# All models have been moved to core_models.py for better organization

from typing import Optional, List, Literal, Generic, TypeVar
from datetime import datetime

# Import all models from the consolidated file
from src.models.core_models import (
    # Core data models
    QuestionData,
    SecurityResponse,
    
    # Input models
    FeatureInput,
    
    # Error models
    AgentError as AgentOutputError,  # Renamed for compatibility
    
    # Response data models
    ChatProgress,
    ChatData,
    FeatureOverview,
    Ticket,
    TicketsData,
    AgentSuccessData,
    AgentOutputData,
    
    # Conversation & session models
    ConversationMessage,
    SessionDataWithConversation,
    
    # Utility models
    HealthData,
    ClearSessionData,
    
    # Generic wrapper
    ApiResponse,
    
    # Specific response types
    HealthResponse,
    SessionWithConversationResponse,
    AgentOutput,
    ClearSessionResponse,
    
    # Type variable
    T
)

# Re-export all models for backward compatibility
__all__ = [
    'QuestionData',
    'FeatureInput', 
    'AgentOutputError',
    'ChatProgress',
    'ChatData',
    'FeatureOverview',
    'Ticket',
    'TicketsData',
    'ConversationMessage',
    'SessionDataWithConversation',
    'AgentOutputData',
    'HealthData',
    'ClearSessionData',
    'ApiResponse',
    'HealthResponse',
    'SessionWithConversationResponse',
    'AgentOutput',
    'ClearSessionResponse',
    'T'
] 