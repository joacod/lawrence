import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.chat_models import ChatOllama
from src.config.settings import settings
from src.utils.logger import setup_logger
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

    def _extract_questions_from_markdown(self, text: str) -> list:
        """Extract QUESTIONS section from markdown block and convert to list of dicts."""
        import re
        match = re.search(r'QUESTIONS:\s*\n(.*?)(?=\n\w+:|$)', text, re.DOTALL)
        if not match:
            raise ValueError("No QUESTIONS section found in response")
        section = match.group(1)
        questions = []
        current = {}
        for line in section.splitlines():
            line = line.strip()
            if line.startswith('- question:'):
                if current:
                    questions.append(current)
                current = {"question": line[len('- question:'):].strip().strip('"')}
            elif line.startswith('status:'):
                current["status"] = line[len('status:'):].strip().strip('"')
            elif line.startswith('user_answer:'):
                val = line[len('user_answer:'):].strip()
                if val.lower() == 'null':
                    current["user_answer"] = None
                else:
                    current["user_answer"] = val.strip('"')
        if current:
            questions.append(current)
        return questions

    async def analyze(self, pending_questions: list, user_followup: str) -> str:
        logger.info("Question analysis agent evaluating user follow-up against pending questions")
        pending_questions_str = json.dumps(pending_questions, ensure_ascii=False)
        result = await self.chain.ainvoke({
            "pending_questions": pending_questions_str,
            "user_followup": user_followup
        })
        return result.content 