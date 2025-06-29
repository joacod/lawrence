import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.chat_models import ChatOllama
from src.config.settings import settings
from src.utils.logger import setup_logger

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
        system_prompt = """
You are a Question Analysis Agent for a Product Owner AI system.

You will be given:
- The list of pending questions (with their status and any previous user answers)
- The user's follow-up message

For each question:
- If the user has provided a clear answer, even if paraphrased, set status to "answered" and extract the answer.
- If the user has clearly disregarded or rejected the question (e.g., says "no", "not needed", "just X", "skip", etc.), set status to "disregarded".
- If the user did not address the question, leave status as "pending".

EXAMPLES:
Questions:
- "Will there be any additional authentication factors required, like two-factor authentication or biometrics?"
User: "No additional authentication factors required."
Output: [{{"question": "...", "status": "disregarded", "user_answer": null}}]

Questions:
- "Will there be any additional authentication factors required, like two-factor authentication or biometrics?"
User: "Just email and password, nothing else."
Output: [{{"question": "...", "status": "disregarded", "user_answer": null}}]

Questions:
- "Will there be any additional authentication factors required, like two-factor authentication or biometrics?"
User: "Yes, add two-factor authentication using SMS."
Output: [{{"question": "...", "status": "answered", "user_answer": "yes, using SMS"}}]

Questions:
- "Will there be any additional authentication factors required, like two-factor authentication or biometrics?"
User: "I want a dashboard with charts."
Output: [{{"question": "...", "status": "pending", "user_answer": null}}]

Your response MUST be a valid JSON array as described above. DO NOT include any other text before or after the JSON.
"""
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """PENDING QUESTIONS:\n{pending_questions}\n\nUSER FOLLOW-UP:\n{user_followup}""")
        ])
        self.chain = self.prompt | self.llm

    def _extract_json_from_text(self, text: str):
        try:
            start = text.index('[')
            end = text.rindex(']') + 1
            return json.loads(text[start:end])
        except Exception:
            raise ValueError(f"Could not extract JSON array from: {text}")

    async def analyze(self, pending_questions: list, user_followup: str) -> list:
        logger.info("Question analysis agent evaluating user follow-up against pending questions")
        pending_questions_str = json.dumps(pending_questions, ensure_ascii=False)
        result = await self.chain.ainvoke({
            "pending_questions": pending_questions_str,
            "user_followup": user_followup
        })
        try:
            return self._extract_json_from_text(result.content)
        except Exception as e:
            logger.error(f"Failed to parse question analysis agent response: {result.content}")
            return [] 