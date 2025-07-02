import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.chat_models import ChatOllama
from src.config.settings import settings
from src.utils.logger import setup_logger
from src.utils.parsers.question_parser import parse_questions_section
import os

logger = setup_logger(__name__)

class QuestionAnalysisAgent:
    def __init__(self):
        self.llm = ChatOllama(
            model=settings.QUESTION_ANALYSIS_MODEL,
            base_url="http://localhost:11434",
            timeout=120,
            temperature=0.1,
            num_ctx=2048,
        )
        prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'question_analysis_agent_prompt.txt')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """PENDING QUESTIONS:\n{pending_questions}\n\nUSER FOLLOW-UP:\n{user_followup}""")
        ])
        self.chain = self.prompt | self.llm

    # Removed: _extract_questions_from_markdown - now using parse_questions_section from utils

    async def analyze(self, pending_questions: list, user_followup: str) -> str:
        logger.info("Question analysis agent evaluating user follow-up against pending questions")
        pending_questions_str = json.dumps(pending_questions, ensure_ascii=False)
        result = await self.chain.ainvoke({
            "pending_questions": pending_questions_str,
            "user_followup": user_followup
        })
        return result.content 