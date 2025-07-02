"""
Base Agent Class
Provides common functionality for all agents including LLM setup,
prompt loading, error handling, and response processing.
"""
import os
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.chat_models import ChatOllama
from src.utils.logger import setup_logger
from .agent_config import AgentConfigRegistry, AgentConfig
from src.utils.agents_response_parser import AgentResponseParserFactory


class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(self, agent_type: str):
        """Initialize the base agent with configuration and setup."""
        self.agent_type = agent_type
        self.logger = setup_logger(self.__class__.__name__)
        
        # Get configuration for this agent type
        self.config = AgentConfigRegistry.get_config(agent_type)
        
        # Initialize LLM with configuration
        self.llm = ChatOllama(**self.config.to_llm_kwargs())
        
        # Load prompt template
        self.prompt = self._load_prompt_template()
        
        # Create chain
        self.chain = self.prompt | self.llm
        
        # Get response parser
        self.parser = AgentResponseParserFactory.get_parser(agent_type)
        
        self.logger.info(f"Initialized {agent_type} agent with model {self.config.model}")
    
    def _load_prompt_template(self) -> ChatPromptTemplate:
        """Load and create the prompt template for this agent."""
        prompt_filename = f"{self.agent_type}_agent_prompt.txt"
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'prompts', 
            prompt_filename
        )
        
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read()
        
        return self._create_prompt_template(system_prompt)
    
    @abstractmethod
    def _create_prompt_template(self, system_prompt: str) -> ChatPromptTemplate:
        """Create the specific prompt template for this agent."""
        pass
    
    async def _invoke_with_retry(self, input_data: Dict[str, Any]) -> str:
        """Invoke the agent with retry logic based on configuration."""
        last_exception = None
        
        for attempt in range(self.config.retry_attempts):
            try:
                self.logger.info(f"Invoking {self.agent_type} agent (attempt {attempt + 1})")
                result = await self.chain.ainvoke(input_data)
                self.logger.debug(f"Raw response from {self.agent_type} agent: {result.content}")
                return result.content
                
            except Exception as e:
                last_exception = e
                self.logger.warning(
                    f"Attempt {attempt + 1} failed for {self.agent_type} agent: {str(e)}"
                )
                
                if attempt < self.config.retry_attempts - 1:
                    self.logger.info(f"Retrying {self.agent_type} agent...")
                else:
                    self.logger.error(f"All retry attempts failed for {self.agent_type} agent")
        
        # If all retries failed, raise the last exception
        raise last_exception
    
    async def _process_response(self, response_content: str) -> Dict[str, Any]:
        """Process the raw response content using the appropriate parser."""
        try:
            return self.parser.parse(response_content)
        except Exception as e:
            self.logger.error(f"Failed to parse {self.agent_type} agent response: {str(e)}")
            self.logger.error(f"Raw response: {response_content}")
            raise ValueError(f"Failed to parse {self.agent_type} agent response: {str(e)}")
    
    async def _retry_with_format_reminder(self, original_input: Dict[str, Any], failed_response: str) -> str:
        """Retry with explicit format reminder when parsing fails."""
        format_reminder = self._get_format_reminder_prompt(failed_response)
        
        self.logger.info(f"Retrying {self.agent_type} agent with format reminder")
        
        # Try once more with format reminder
        result = await self.chain.ainvoke({
            **original_input,
            "input": format_reminder
        })
        
        return result.content
    
    def _get_format_reminder_prompt(self, failed_response: str) -> str:
        """Get format reminder prompt for this agent type."""
        return self._load_retry_prompt_template(failed_response)
    
    def _load_retry_prompt_template(self, failed_response: str) -> str:
        """Load retry prompt template from file."""
        # Try agent-specific retry prompt first
        retry_filename = f"{self.agent_type}_agent_retry.txt"
        retry_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'prompts', 
            'retry',
            retry_filename
        )
        
        # Fall back to default retry prompt if agent-specific doesn't exist
        if not os.path.exists(retry_path):
            retry_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                'prompts', 
                'retry',
                'default_retry.txt'
            )
        
        if not os.path.exists(retry_path):
            # Ultimate fallback - basic inline template
            return f"""You did not follow the required format. Please respond in the EXACT format specified in your instructions.

Your previous response was:
{failed_response}

Please provide a properly formatted response following your system instructions."""
        
        with open(retry_path, 'r', encoding='utf-8') as f:
            retry_template = f.read()
        
        # Format the template with the failed response
        return retry_template.format(failed_response=failed_response)
    
    async def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main invoke method with full error handling and parsing."""
        try:
            # Invoke with retry logic
            response_content = await self._invoke_with_retry(input_data)
            
            # Process response through parser
            try:
                parsed_response = await self._process_response(response_content)
            except ValueError as parse_error:
                # If parsing fails, try once with format reminder
                if "Failed to parse" in str(parse_error):
                    self.logger.warning(f"Format parsing failed, trying with format reminder")
                    try:
                        retry_response = await self._retry_with_format_reminder(input_data, response_content)
                        parsed_response = await self._process_response(retry_response)
                        self.logger.info(f"{self.agent_type} agent completed successfully after format retry")
                    except Exception as retry_error:
                        self.logger.error(f"Format retry also failed: {str(retry_error)}")
                        raise parse_error  # Raise the original parsing error
                else:
                    raise
            
            self.logger.info(f"{self.agent_type} agent completed successfully")
            return parsed_response
            
        except Exception as e:
            self.logger.error(f"Error in {self.agent_type} agent: {str(e)}", exc_info=True)
            raise
    
    @abstractmethod
    async def process(self, *args, **kwargs) -> Any:
        """Main processing method - implemented by each specific agent."""
        pass


class SimpleAgent(BaseAgent):
    """Base class for agents with simple human input prompts."""
    
    def _create_prompt_template(self, system_prompt: str) -> ChatPromptTemplate:
        """Create a simple system + human prompt template."""
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}")
        ])


class ConversationalAgent(BaseAgent):
    """Base class for agents that need conversation history (like POAgent)."""
    
    def _create_prompt_template(self, system_prompt: str) -> ChatPromptTemplate:
        """Create a prompt template with conversation history support."""
        from langchain_core.prompts import MessagesPlaceholder
        
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])


class ContextualAgent(BaseAgent):
    """Base class for agents that need contextual input (like ContextAgent, QuestionAnalysisAgent)."""
    
    def _create_prompt_template(self, system_prompt: str) -> ChatPromptTemplate:
        """Create a prompt template with contextual input support."""
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", self._get_contextual_template())
        ])
    
    @abstractmethod
    def _get_contextual_template(self) -> str:
        """Get the contextual input template for this agent."""
        pass 