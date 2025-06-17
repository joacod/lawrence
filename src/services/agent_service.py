from typing import Dict, List
import json
import uuid
import logging
import sys
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_ollama.chat_models import ChatOllama
from src.config.settings import settings
from src.utils.response_parser import parse_response_to_json

# Configure logging with immediate console output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self):
        # Main conversation model
        self.llm = ChatOllama(model=settings.MODEL_NAME)
        
        # Main conversation prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an AI-powered Product Owner Assistant focused on clarifying software features and generating documentation. When a user describes a feature:
            1. Analyze the feature and, if vague, ask up to 3 specific clarifying questions.
            2. Your response MUST follow this exact format with no additional text before or after:
            
            RESPONSE:
            [Your conversational response to the user - DO NOT include any questions here]

            PENDING QUESTIONS:
            [List your clarifying questions here, one per line starting with -]

            MARKDOWN:
            # Feature: [Feature Name]

            ## Description
            [Detailed description of the feature and its purpose]

            ## Acceptance Criteria
            [List of specific, testable criteria that define when the feature is complete]

            ## Backend Changes
            [List of required backend changes, or "No changes needed" if none required]

            ## Frontend Changes
            [List of required frontend changes, or "No changes needed" if none required]

            IMPORTANT: 
            - Do not add any text before RESPONSE or after the markdown section
            - Do not include any conversational elements or additional explanations
            - Keep the RESPONSE conversational but without questions
            - Put ALL clarifying questions in the PENDING QUESTIONS section only
            - Use only - for bullet points in PENDING QUESTIONS"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        self.chain = self.prompt | self.llm
        self.sessions: Dict[str, List] = {}

    async def process_feature(self, feature: str, session_id: str | None = None) -> tuple[str, str, str, list[str]]:
        session_id = session_id or str(uuid.uuid4())
        
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        chat_history = self.sessions[session_id]
        
        try:
            # Get conversational response
            logger.info("Getting conversational response from model")
            result = await self.chain.ainvoke({
                "chat_history": chat_history,
                "input": feature
            })
            logger.info("Model raw response:")
            logger.info(result.content)
            
            try:
                # Try to parse the response into JSON
                output = parse_response_to_json(result.content)
            except ValueError as e:
                # If parsing fails, log the error and raw response for debugging
                logger.error("Failed to parse response:", exc_info=True)
                logger.error("Raw response that failed to parse:")
                logger.error("---START OF FAILED RESPONSE---")
                logger.error(result.content)
                logger.error("---END OF FAILED RESPONSE---")
                
                # Retry with a more explicit prompt
                logger.info("Retrying with explicit format reminder")
                retry_prompt = f"""Please provide your response in the exact format specified:

RESPONSE:
[Your conversational response here]

PENDING QUESTIONS:
[Your questions here]

MARKDOWN:
[Your markdown content here]

Previous response that needs to be reformatted:
{result.content}"""
                
                retry_result = await self.chain.ainvoke({
                    "chat_history": chat_history,
                    "input": retry_prompt
                })
                logger.info("Retry model response:")
                logger.info(retry_result.content)
                
                # Try parsing the retry response
                try:
                    output = parse_response_to_json(retry_result.content)
                except ValueError as e:
                    logger.error("Failed to parse retry response:", exc_info=True)
                    logger.error("Raw retry response that failed to parse:")
                    logger.error("---START OF FAILED RETRY RESPONSE---")
                    logger.error(retry_result.content)
                    logger.error("---END OF FAILED RETRY RESPONSE---")
                    raise
            
            # Update chat history
            chat_history.append(HumanMessage(content=feature))
            chat_history.append(AIMessage(content=json.dumps(output)))
            
            if len(chat_history) > settings.MAX_HISTORY_LENGTH:
                chat_history = chat_history[-settings.MAX_HISTORY_LENGTH:]
            
            self.sessions[session_id] = chat_history
            
            return session_id, output["response"], output["markdown"], output["questions"]
            
        except Exception as e:
            logger.error("Error in process_feature:", exc_info=True)
            logger.error(f"Session ID: {session_id}")
            logger.error(f"Feature input: {feature}")
            raise

    def clear_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False 