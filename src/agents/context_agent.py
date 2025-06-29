import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.chat_models import ChatOllama
from src.config.settings import settings
from src.utils.logger import setup_logger

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
        system_prompt = """
You are a Context Validation Agent for a Product Owner AI system.

You will be given:
- The current feature description
- The list of pending clarifying questions
- The user's follow-up message

RULES:
- If the follow-up is a direct answer (including a negative, paraphrased, or partial answer) to any pending question, it is contextually relevant.
- If the follow-up adds, clarifies, or modifies details about the original feature, it is contextually relevant.
- If the follow-up is unrelated to the feature or questions, it is NOT contextually relevant.

EXAMPLES:
Pending: "Will there be any additional authentication factors required, like two-factor authentication or biometrics?"
User: "No additional authentication factors required."
→ Contextually relevant (negative answer)

Pending: "Will there be any additional authentication factors required, like two-factor authentication or biometrics?"
User: "Just email and password, nothing else."
→ Contextually relevant (negative answer)

Pending: "Will there be any additional authentication factors required, like two-factor authentication or biometrics?"
User: "Yes, add two-factor authentication using SMS."
→ Contextually relevant (positive answer)

Pending: "Will there be any additional authentication factors required, like two-factor authentication or biometrics?"
User: "I want a dashboard with charts."
→ NOT contextually relevant

Your response MUST be a valid JSON object:
{{
  "is_contextually_relevant": true,
  "reasoning": "Brief explanation."
}}
DO NOT include any other text before or after the JSON.
"""
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """PENDING QUESTIONS:\n{pending_questions}\n\nUSER FOLLOW-UP:\n{user_followup}""")
        ])
        self.chain = self.prompt | self.llm

    def _extract_json_from_text(self, text: str) -> dict:
        try:
            start = text.index('{')
            end = text.rindex('}') + 1
            return json.loads(text[start:end])
        except Exception:
            raise ValueError(f"Could not extract JSON from: {text}")

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
            response_data = self._extract_json_from_text(result.content)
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