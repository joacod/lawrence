from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.chat_models import ChatOllama
from src.config.settings import settings
from src.utils.logger import setup_logger
import os

logger = setup_logger(__name__)

class ContextAgent:
    def __init__(self):
        self.llm = ChatOllama(
            model=settings.CONTEXT_MODEL,
            base_url="http://localhost:11434",
            timeout=120,
            temperature=0.1,
            num_ctx=2048,
        )
        prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'context_agent_prompt.txt')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """PENDING QUESTIONS:\n{pending_questions}\n\nUSER FOLLOW-UP:\n{user_followup}""")
        ])
        self.chain = self.prompt | self.llm

    def _extract_context_from_markdown(self, text: str) -> dict:
        """Extract CONTEXT section from markdown block and convert to dict."""
        import re
        match = re.search(r'CONTEXT:\s*\n(.*?)(?=\n\w+:|$)', text, re.DOTALL)
        if not match:
            raise ValueError("No CONTEXT section found in response")
        section = match.group(1)
        result = {}
        for line in section.splitlines():
            if ':' in line:
                key, value = line.split(':', 1)
                result[key.strip()] = value.strip()
        is_contextually_relevant = result.get('is_contextually_relevant', '').lower() == 'true'
        reasoning = result.get('reasoning', '')
        return {
            "is_contextually_relevant": is_contextually_relevant,
            "reasoning": reasoning
        }

    def _format_pending_questions(self, session_history: dict) -> str:
        # Only show the most recent assistant's pending questions
        for msg in reversed(session_history.get("conversation", [])):
            if msg["type"] == "assistant" and msg.get("questions"):
                return "\n".join([
                    f"- {q['question']} (status: {q.get('status', 'pending')})" for q in msg["questions"]
                ])
        return ""

    async def evaluate_context(self, session_history: dict, user_followup: str) -> dict:
        logger.info("Context agent evaluating follow-up context")
        pending_questions_str = self._format_pending_questions(session_history)
        result = await self.chain.ainvoke({
            "pending_questions": pending_questions_str,
            "user_followup": user_followup
        })
        try:
            response_data = self._extract_context_from_markdown(result.content)
        except Exception as e:
            logger.error(f"Failed to parse context agent response: {result.content}")
            return {
                "is_contextually_relevant": False,
                "reasoning": "Failed to parse context agent response"
            }
        if not all(k in response_data for k in ["is_contextually_relevant", "reasoning"]):
            logger.error(f"Invalid context agent response format: {response_data}")
            return {
                "is_contextually_relevant": False,
                "reasoning": "Invalid context agent response format"
            }
        return response_data 