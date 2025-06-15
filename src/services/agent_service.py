from typing import Dict, List
import json
import uuid
import logging
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_ollama.chat_models import ChatOllama
from src.config.settings import settings
from src.utils.response_parser import parse_response_to_json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self):
        # Main conversation model
        self.llm = ChatOllama(model=settings.MODEL_NAME)
        
        # Main conversation prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an AI-powered Product Owner Assistant. Your goal is to clarify software features and generate documentation. When a user describes a feature:
            1. Analyze the feature and, if vague, ask up to 3 specific clarifying questions.
            2. Provide a clear response with the following sections:
               - RESPONSE: Your conversational response to the user, including any clarifying questions
               - MARKDOWN: A formatted markdown document with 'Feature', 'Details', and 'Pending Questions' sections
            
            Keep your response natural and conversational, but make sure to clearly separate the sections using the titles above."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        self.chain = self.prompt | self.llm
        self.sessions: Dict[str, List] = {}

    async def process_feature(self, feature: str, session_id: str | None = None) -> tuple[str, str, str]:
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
            
            # Parse the response into JSON
            output = parse_response_to_json(result.content)
            
            # Update chat history
            chat_history.append(HumanMessage(content=feature))
            chat_history.append(AIMessage(content=json.dumps(output)))
            
            if len(chat_history) > settings.MAX_HISTORY_LENGTH:
                chat_history = chat_history[-settings.MAX_HISTORY_LENGTH:]
            
            self.sessions[session_id] = chat_history
            
            return session_id, output["response"], output["markdown"]
            
        except Exception as e:
            logger.error(f"Error in process_feature: {str(e)}")
            logger.error("Full error details:", exc_info=True)
            raise

    def clear_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False 