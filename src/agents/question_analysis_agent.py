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

Your response MUST be a markdown block with the following format:
RESPONSE:
[Short summary of the question analysis.]

QUESTIONS:
- question: "..."
  status: "..."
  user_answer: "..."
- question: "..."
  status: "..."
  user_answer: null

- Do NOT include any extra text, comments, or explanations outside the markdown block.
- Do NOT use code blocks, markdown headers, or any formatting other than the above.

EXAMPLE OUTPUT:
RESPONSE:
The user answered the first question and disregarded the second.

QUESTIONS:
- question: "Will there be any additional authentication factors required, like two-factor authentication or biometrics?"
  status: "answered"
  user_answer: "yes, using SMS"
- question: "Is there a dashboard?"
  status: "pending"
  user_answer: null
"""
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

    async def analyze(self, pending_questions: list, user_followup: str) -> list:
        logger.info("Question analysis agent evaluating user follow-up against pending questions")
        pending_questions_str = json.dumps(pending_questions, ensure_ascii=False)
        result = await self.chain.ainvoke({
            "pending_questions": pending_questions_str,
            "user_followup": user_followup
        })
        try:
            return self._extract_questions_from_markdown(result.content)
        except Exception as e:
            logger.error(f"Failed to parse question analysis agent response: {result.content}")
            return [] 