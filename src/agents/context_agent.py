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

Your response MUST be a markdown block with the following format:
RESPONSE:
[Short summary of the context evaluation.]

CONTEXT:
is_contextually_relevant: true or false
reasoning: Brief explanation.

- Do NOT include any extra text, comments, or explanations outside the markdown block.
- Do NOT use code blocks, markdown headers, or any formatting other than the above.

EXAMPLE OUTPUT:
RESPONSE:
The follow-up directly answers a pending question.

CONTEXT:
is_contextually_relevant: true
reasoning: The follow-up directly answers a pending question.
"""
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