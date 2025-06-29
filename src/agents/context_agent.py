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
You are a Context Validation Agent for a Software Product Management system. Your job is to determine if a user's follow-up request is contextually relevant to the current feature session.

You will be given:
- The full session history (including all user and assistant messages, questions, answers, and their status)
- The user's follow-up request

RULES:
- If the follow-up is a direct answer to any pending or previously asked question, it is contextually relevant. This includes both positive and negative answers (e.g., "no multi-factor authentication" is a valid answer to "Will the system support multi-factor authentication?").
- If the follow-up adds, clarifies, or modifies details about the original feature, it is contextually relevant.
- If the follow-up is unrelated to the feature or questions, it is NOT contextually relevant.

EXAMPLES:
- Question: "Will the system support multi-factor authentication?"  
  Follow-up: "No multi-factor authentication"  
  → Contextually relevant (negative answer)
- Question: "Should we allow users to reset their passwords?"  
  Follow-up: "Yes, allow password reset"  
  → Contextually relevant (positive answer)
- Question: "Should we allow users to reset their passwords?"  
  Follow-up: "I want a dashboard with charts"  
  → NOT contextually relevant

Present the session history as a readable conversation log.

Your response MUST be a valid JSON object with EXACTLY these fields:
{{
  "is_contextually_relevant": true,
  "reasoning": "Brief explanation of your decision."
}}
DO NOT include any other text before or after the JSON.
"""
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """SESSION HISTORY:\n{session_history}\n\nUSER FOLLOW-UP: {user_followup}""")
        ])
        self.chain = self.prompt | self.llm

    def _extract_json_from_text(self, text: str) -> dict:
        try:
            start = text.index('{')
            end = text.rindex('}') + 1
            return json.loads(text[start:end])
        except Exception:
            raise ValueError(f"Could not extract JSON from: {text}")

    def _format_session_history(self, session_history: dict) -> str:
        # Format the session history for readability
        lines = []
        for msg in session_history.get("conversation", []):
            if msg["type"] == "user":
                lines.append(f"User: {msg['content']}")
            elif msg["type"] == "assistant":
                lines.append(f"Assistant: {msg.get('response', '')}")
                if msg.get("questions"):
                    for q in msg["questions"]:
                        qtext = q["question"] if isinstance(q, dict) else str(q)
                        status = q.get("status", "pending") if isinstance(q, dict) else "pending"
                        answer = q.get("user_answer") if isinstance(q, dict) else None
                        lines.append(f"  - Q: {qtext} (status: {status})" + (f" | Answer: {answer}" if answer else ""))
        return "\n".join(lines)

    async def evaluate_context(self, session_history: dict, user_followup: str) -> dict:
        logger.info("Context agent evaluating follow-up context")
        formatted_history = self._format_session_history(session_history)
        # Fallback: if follow-up contains 'no' or 'not' and matches a pending question subject, treat as relevant
        for msg in session_history.get("conversation", []):
            if msg["type"] == "assistant" and msg.get("questions"):
                for q in msg["questions"]:
                    q_main = q["question"].split('?')[0].strip().lower() if isinstance(q, dict) else str(q).split('?')[0].strip().lower()
                    status = q.get("status", "pending") if isinstance(q, dict) else "pending"
                    if status == 'pending' and (
                        (q_main in user_followup.lower() and any(neg in user_followup.lower() for neg in ['no', 'not']))
                    ):
                        return {
                            "is_contextually_relevant": True,
                            "reasoning": "Follow-up is a direct (negative) answer to a pending question."
                        }
        result = await self.chain.ainvoke({
            "session_history": formatted_history,
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