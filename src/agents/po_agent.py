from typing import List
import json
from datetime import datetime, timezone
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_ollama.chat_models import ChatOllama
from src.config.settings import settings
from src.utils.response_parser import parse_response_to_json, parse_questions_section
from src.core.session_manager import SessionManager
from src.core.storage_manager import StorageManager
from src.utils.logger import setup_logger
from src.agents.question_analysis_agent import QuestionAnalysisAgent
import os

logger = setup_logger(__name__)

class POAgent:
    def __init__(self):
        # Main conversation model
        self.llm = ChatOllama(
            model=settings.PO_MODEL,
            base_url="http://localhost:11434",
            timeout=180,  # 3 minutes timeout for longer responses
            temperature=0.7,  # Higher temperature for creative responses
            num_ctx=4096,  # Larger context window for conversation history
        )
        prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'po_agent_prompt.txt')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read()
        # Main conversation prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        self.chain = self.prompt | self.llm
        self.session_manager = SessionManager()
        self.storage_manager = StorageManager()
        self.question_analysis_agent = QuestionAnalysisAgent()

    async def process_feature(self, feature: str, session_id: str | None = None) -> tuple[str, str, str, str, list, int, int, datetime, datetime]:
        session_id = self.session_manager.create_session(session_id)
        created_at, updated_at = self.session_manager.get_session_timestamps(session_id)
        chat_history = self.session_manager.get_chat_history(session_id)

        # Use QuestionAnalysisAgent to update pending questions
        pending_questions = self.storage_manager.get_pending_questions(session_id)
        if pending_questions:
            analysis_markdown = await self.question_analysis_agent.analyze(pending_questions, feature)
            analysis = parse_questions_section(analysis_markdown)
            for result in analysis:
                q_text = result.get("question")
                status = result.get("status")
                user_answer = result.get("user_answer")
                if status == "answered":
                    self.storage_manager.answer_question(session_id, q_text, user_answer or feature)
                elif status == "disregarded":
                    self.storage_manager.disregard_question(session_id, q_text)
                # If pending, do nothing

        try:
            logger.info("Getting conversational response from model")
            result = await self.chain.ainvoke({
                "chat_history": chat_history,
                "input": feature
            })
            logger.info("Model raw response:")
            logger.info(result.content)
            try:
                output = parse_response_to_json(result.content)
                # Ensure RESPONSE is not empty; if it is, retry with explicit reminder
                if not output["response"].strip():
                    logger.warning("Model output had empty RESPONSE section. Retrying with explicit format reminder.")
                    retry_prompt = (
                        "You MUST provide a non-empty conversational RESPONSE section. "
                        "If you do not, the system will fail. "
                        "RESPONSE:\n[Your conversational response to the user - DO NOT include any questions here]\n\n"
                        "PENDING QUESTIONS:\n[List your clarifying questions here, one per line starting with -]\n\n"
                        "MARKDOWN:\n[Your markdown content here]\n\n"
                        f"Previous response that needs to be reformatted:\n{result.content}"
                    )
                    retry_result = await self.chain.ainvoke({
                        "chat_history": chat_history,
                        "input": retry_prompt
                    })
                    logger.info("Retry model response (RESPONSE was empty):")
                    logger.info(retry_result.content)
                    output = parse_response_to_json(retry_result.content)
                    if not output["response"].strip():
                        output["response"] = "Sorry, I was unable to generate a response. Please try again or rephrase your request."
            except ValueError as e:
                logger.error("Failed to parse response:", exc_info=True)
                logger.error("Raw response that failed to parse:")
                logger.error("---START OF FAILED RESPONSE---")
                logger.error(result.content)
                logger.error("---END OF FAILED RESPONSE---")
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
                try:
                    output = parse_response_to_json(retry_result.content)
                except ValueError as e:
                    logger.error("Failed to parse retry response:", exc_info=True)
                    logger.error("Raw retry response that failed to parse:")
                    logger.error("---START OF FAILED RETRY RESPONSE---")
                    logger.error(retry_result.content)
                    logger.error("---END OF FAILED RETRY RESPONSE---")
                    raise

            # Store and update questions in StorageManager
            new_questions = output.get("questions", [])
            if new_questions and isinstance(new_questions[0], str):
                self.storage_manager.add_questions(session_id, new_questions)
            elif new_questions and isinstance(new_questions[0], dict):
                self.storage_manager.set_questions(session_id, new_questions)

            # Always include all questions with their status and user_answer
            all_questions = self.storage_manager.get_questions(session_id)
            output["questions"] = all_questions

            # Calculate progress
            total_questions = len(all_questions)
            answered_questions = sum(1 for q in all_questions if q["status"] in ("answered", "disregarded"))

            # Extract title from markdown if this is a new session
            title = self._extract_title_from_markdown(output["markdown"], session_id)
            chat_history.append(HumanMessage(content=feature))
            chat_history.append(AIMessage(content=json.dumps(output)))
            if len(chat_history) > settings.MAX_HISTORY_LENGTH:
                chat_history = chat_history[-settings.MAX_HISTORY_LENGTH:]
            self.session_manager.update_chat_history(session_id, chat_history)
            return session_id, title, output["response"], output["markdown"], output["questions"], total_questions, answered_questions, created_at, updated_at
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