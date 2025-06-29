import re
import os
from typing import Optional, Dict, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.chat_models import ChatOllama
from src.config.settings import settings
from src.models.agent_response import SecurityResponse
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class SecurityAgent:
    def __init__(self):
        """Initialize the Security Agent with the LLM model and prompt template."""
        self.llm = ChatOllama(
            model=settings.SECURITY_MODEL,
            base_url="http://localhost:11434",
            timeout=120,  # 2 minutes timeout
            temperature=0.1,  # Low temperature for consistent classification
            num_ctx=2048,  # Context window size
        )
        prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'security_agent_prompt.txt')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}")
        ])
        self.chain = self.prompt | self.llm

    def _extract_security_from_markdown(self, text: str) -> dict:
        """Extract SECURITY section from markdown block and convert to dict."""
        # Find SECURITY section
        match = re.search(r'SECURITY:\s*\n(.*?)(?=\n\w+:|$)', text, re.DOTALL)
        if not match:
            raise ValueError("No SECURITY section found in response")
        section = match.group(1)
        # Parse key-value pairs
        result = {}
        for line in section.splitlines():
            if ':' in line:
                key, value = line.split(':', 1)
                result[key.strip()] = value.strip()
        # Type conversions
        is_feature_request = result.get('is_feature_request', '').lower() == 'true'
        try:
            confidence = float(result.get('confidence', 1.0))
        except Exception:
            confidence = 1.0
        reasoning = result.get('reasoning', '')
        return {
            "is_feature_request": is_feature_request,
            "confidence": confidence,
            "reasoning": reasoning
        }

    async def evaluate_request(self, user_input: str, session_context: Optional[Dict] = None) -> SecurityResponse:
        """
        Evaluate if the user input is a valid software product management related request.
        Args:
            user_input (str): The user's input text to evaluate
            session_context (Optional[Dict]): Context about the current session (ignored for security check)
        Returns:
            SecurityResponse: Object containing the evaluation results
        """
        logger.info("Security agent evaluating request")
        result = await self.chain.ainvoke({"input": user_input})
        try:
            response_data = self._extract_security_from_markdown(result.content)
        except Exception as e:
            logger.error(f"Failed to parse model response: {result.content}")
            return SecurityResponse(
                is_feature_request=False,
                confidence=1.0,
                reasoning="Failed to parse security evaluation response"
            )
        if not all(k in response_data for k in ["is_feature_request", "confidence", "reasoning"]):
            logger.error(f"Invalid response format: {response_data}")
            return SecurityResponse(
                is_feature_request=False,
                confidence=1.0,
                reasoning="Invalid security evaluation response format"
            )
        return SecurityResponse(
            is_feature_request=response_data["is_feature_request"],
            confidence=float(response_data["confidence"]),
            reasoning=response_data["reasoning"]
        ) 