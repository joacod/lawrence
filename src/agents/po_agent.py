"""
PO Agent
Product Owner agent for feature clarification and documentation.
Uses the base agent framework with conversation history support.
"""
from typing import List
import json
from datetime import datetime, timezone
from langchain_core.messages import HumanMessage, AIMessage
# parse_response_to_json no longer needed - base agent handles parsing automatically
from src.utils.parsers.question_parser import parse_questions_section
from src.utils.parsers.markdown_parser import extract_title_from_markdown
from src.core.session_manager import SessionManager
from src.agents.question_analysis_agent import QuestionAnalysisAgent
from src.config.settings import settings
from .base import ConversationalAgent

class POAgent(ConversationalAgent):
    """
    Product Owner Agent for feature clarification and documentation.
    
    Features:
    - Automatic configuration from AgentConfigRegistry
    - Built-in retry logic and error handling
    - Conversation history support
    - Session management integration
    """
    
    def __init__(self):
        """Initialize POAgent with 'po' configuration."""
        super().__init__(agent_type="po")
        self.session_manager = SessionManager()
        self.question_analysis_agent = QuestionAnalysisAgent()

    async def process_feature(self, feature: str, session_id: str | None = None) -> tuple[str, str, str, str, list, int, int, datetime, datetime]:
        """
        Process a feature request and return comprehensive response data.
        
        Args:
            feature (str): The feature description
            session_id (str | None): Optional session ID
            
        Returns:
            tuple: (session_id, title, response, markdown, questions, total_questions, answered_questions, created_at, updated_at)
        """
        session_id = self.session_manager.create_session(session_id)
        created_at, updated_at = self.session_manager.get_session_timestamps(session_id)
        chat_history = self.session_manager.get_chat_history(session_id)

        # Check if this is a follow-up to existing questions
        existing_questions = self.session_manager.get_questions(session_id)
        is_followup = len(existing_questions) > 0 and len(chat_history) > 0
        
        if is_followup:
            self.logger.info("Processing follow-up response to existing questions")
            # Use QuestionAnalysisAgent to update pending questions
            pending_questions = self.session_manager.get_pending_questions(session_id)
            if pending_questions:
                analysis_markdown = await self.question_analysis_agent.analyze(pending_questions, feature)
                analysis = parse_questions_section(analysis_markdown)
                for result in analysis:
                    q_text = result.get("question")
                    status = result.get("status")
                    user_answer = result.get("user_answer")
                    if status == "answered":
                        self.session_manager.answer_question(session_id, q_text, user_answer or feature)
                    elif status == "disregarded":
                        self.session_manager.disregard_question(session_id, q_text)

        try:
            self.logger.info("Getting conversational response from model")
            
            # Use the base agent's invoke method with automatic retry handling
            output = await self.invoke({
                "chat_history": chat_history,
                "input": feature
            })

            # Handle questions based on whether this is a follow-up or new feature
            if is_followup:
                # For follow-ups, only add NEW questions, don't replace existing ones
                new_questions = output.get("questions", [])
                if new_questions and isinstance(new_questions[0], str):
                    self.session_manager.add_questions(session_id, new_questions)
                elif new_questions and isinstance(new_questions[0], dict):
                    # Add only questions that don't already exist
                    existing_question_texts = {q['question'] for q in existing_questions}
                    for new_q in new_questions:
                        if new_q.get('question') not in existing_question_texts:
                            self.session_manager.add_questions(session_id, [new_q['question']])
            else:
                # For new features, set the questions as before
                new_questions = output.get("questions", [])
                if new_questions and isinstance(new_questions[0], str):
                    self.session_manager.add_questions(session_id, new_questions)
                elif new_questions and isinstance(new_questions[0], dict):
                    self.session_manager.set_questions(session_id, new_questions)

            # Always include all questions with their status and user_answer
            all_questions = self.session_manager.get_questions(session_id)
            output["questions"] = all_questions

            # Calculate progress
            total_questions = len(all_questions)
            answered_questions = sum(1 for q in all_questions if q["status"] in ("answered", "disregarded"))

            # Extract title from markdown if this is a new session
            title = self._extract_title_from_markdown(output["markdown"], session_id)
            
            # Update chat history
            chat_history.append(HumanMessage(content=feature))
            chat_history.append(AIMessage(content=json.dumps(output)))
            if len(chat_history) > settings.MAX_HISTORY_LENGTH:
                chat_history = chat_history[-settings.MAX_HISTORY_LENGTH:]
            self.session_manager.update_chat_history(session_id, chat_history)
            
            return session_id, title, output["response"], output["markdown"], output["questions"], total_questions, answered_questions, created_at, updated_at
            
        except Exception as e:
            self.logger.error("Error in process_feature:", exc_info=True)
            self.logger.error(f"Session ID: {session_id}")
            self.logger.error(f"Feature input: {feature}")
            raise

    def _extract_title_from_markdown(self, markdown: str, session_id: str) -> str:
        """Extract title from markdown and set it for the session"""
        # Check if session already has a title
        existing_title = self.session_manager.get_session_title(session_id)
        if existing_title != "Untitled Feature":
            return existing_title
        
        # Use the dedicated markdown parser
        title = extract_title_from_markdown(markdown)
        
        # Set the title for this session
        self.session_manager.set_session_title(session_id, title)
        return title
    
    async def process(self, feature: str, session_id: str | None = None) -> tuple:
        """Main processing method - delegates to process_feature."""
        return await self.process_feature(feature, session_id) 