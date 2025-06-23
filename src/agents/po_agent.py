from typing import List
import json
from datetime import datetime, timezone
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_ollama.chat_models import ChatOllama
from src.config.settings import settings
from src.utils.response_parser import parse_response_to_json
from src.core.session_manager import SessionManager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class POAgent:
    def __init__(self):
        # Main conversation model
        self.llm = ChatOllama(model=settings.PO_MODEL)
        
        # Main conversation prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an AI-powered Product Owner Assistant focused on clarifying software features and generating documentation. When a user describes a feature:
            1. Analyze the feature and, if vague, ask up to 3 specific clarifying questions.
            2. Your response MUST follow this EXACT format with no additional text before or after:
            
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

            CRITICAL FORMAT REQUIREMENTS: 
            - You MUST include the word "MARKDOWN:" before your markdown content
            - You MUST include the word "RESPONSE:" before your conversational response
            - You MUST include the words "PENDING QUESTIONS:" before your questions
            - Do not add any text before RESPONSE or after the markdown section
            - Do not include any conversational elements or additional explanations
            - Keep the RESPONSE conversational but without questions
            - Put ALL clarifying questions in the PENDING QUESTIONS section only
            - Use only - for bullet points in PENDING QUESTIONS
            - The MARKDOWN: section must start with "# Feature:" followed by the feature name"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        self.chain = self.prompt | self.llm
        self.session_manager = SessionManager()

    async def process_feature(self, feature: str, session_id: str | None = None) -> tuple[str, str, str, str, list[str], datetime, datetime]:
        session_id = self.session_manager.create_session(session_id)
        created_at, updated_at = self.session_manager.get_session_timestamps(session_id)
        
        chat_history = self.session_manager.get_chat_history(session_id)
        
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
                retry_prompt = f"""Please provide your response in the EXACT format specified. You MUST include all section headers:

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
            
            # Extract title from markdown if this is a new session
            title = self._extract_title_from_markdown(output["markdown"], session_id)
            
            # Update chat history
            chat_history.append(HumanMessage(content=feature))
            chat_history.append(AIMessage(content=json.dumps(output)))
            
            if len(chat_history) > settings.MAX_HISTORY_LENGTH:
                chat_history = chat_history[-settings.MAX_HISTORY_LENGTH:]
            
            self.session_manager.update_chat_history(session_id, chat_history)
            
            return session_id, title, output["response"], output["markdown"], output["questions"], created_at, updated_at
            
        except Exception as e:
            logger.error("Error in process_feature:", exc_info=True)
            logger.error(f"Session ID: {session_id}")
            logger.error(f"Feature input: {feature}")
            raise

    def _extract_title_from_markdown(self, markdown: str, session_id: str) -> str:
        """Extract title from markdown and set it for the session"""
        # Check if session already has a title
        existing_title = self.session_manager.get_session_title(session_id)
        if existing_title != "Untitled Feature":
            return existing_title
        
        # Extract title from the first line of markdown
        markdown_lines = markdown.split('\n')
        for line in markdown_lines:
            line = line.strip()
            # Look for various markdown header formats
            if line.startswith('# Feature:'):
                title = line.replace('# Feature:', '').strip()
                break
            elif line.startswith('# '):
                # Extract title from any # header (most common case)
                title = line.replace('# ', '').strip()
                break
            elif line.startswith('## '):
                # If no # header found, try ## header
                title = line.replace('## ', '').strip()
                break
        else:
            # If no title found in markdown, use a default
            title = "Untitled Feature"
        
        # Set the title for this session
        self.session_manager.set_session_title(session_id, title)
        return title 