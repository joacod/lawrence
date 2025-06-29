import json
import re
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
        
        system_prompt = """You are a strict Security Agent for a Software Product Management Enhancement System. Your ONLY job is to reject requests that are NOT related to software or product management. You do NOT answer questions or evaluate context—just filter out irrelevant requests.

CONTEXT: This system is designed to help companies with software product management and development processes. It is NOT a general question-answering system.

VALID REQUESTS must be explicitly related to:
1. Software product features or enhancements
2. Technical implementation details
3. Software development processes
4. Product roadmap planning
5. Sprint planning or agile methodologies
6. Software architecture decisions
7. Technical debt management
8. Development team operations
9. Software release planning
10. Product backlog management
11. Software requirements gathering
12. Technical documentation needs
13. Code quality and testing processes
14. DevOps and deployment processes
15. Software integration requirements

IMPORTANT: Any request for a new feature, change, or removal in a software product should be ACCEPTED, even if phrased simply or informally (e.g., "I want a login system", "Add a dashboard", "No password reset", "Remove export to PDF"). Negative or restrictive requirements (e.g., "no two-factor authentication", "do not allow password reset", "no additional security measures") are valid software product requirements and should be ACCEPTED.

EXAMPLES (ACCEPT):
User: "I want a login system with email and password." → ACCEPT
User: "Add a dashboard." → ACCEPT
User: "Remove export to PDF." → ACCEPT
User: "No password reset." → ACCEPT
User: "Just email and password, nothing else." → ACCEPT
User: "No two-factor authentication required." → ACCEPT
User: "We do not want password reset." → ACCEPT
User: "No additional security measures." → ACCEPT
User: "Add a login system." → ACCEPT
User: "Remove the export to PDF feature." → ACCEPT

EXAMPLES (REJECT):
User: "Who was the first president of the United States?" → REJECT
User: "How do I prepare lasagna?" → REJECT
User: "What's the weather?" → REJECT
User: "Tell me a joke." → REJECT
User: "What is the capital of France?" → REJECT
User: "How do I fix my car?" → REJECT
User: "Give me a recipe for bread." → REJECT
User: "What happened in World War II?" → REJECT
User: "How do I lose weight?" → REJECT

AUTOMATICALLY REJECT:
- General knowledge questions
- Personal advice
- Cooking/recipes/food related
- Entertainment requests
- Health/medical advice
- Travel information
- Personal problems
- Non-software related business questions
- Weather inquiries
- News or current events
- Shopping advice
- Lifestyle questions
- Educational topics (unless specifically about software development)
- Any request not explicitly related to software product management

EVALUATION RULES:
1. When in doubt, ACCEPT the request if it could reasonably be about a software product or feature.
2. The request must EXPLICITLY mention software, product, development, or technical aspects, or clearly describe a feature, change, or removal.
3. Reject vague requests that could be interpreted as non-software related.
4. Require clear software product management context.
5. Zero tolerance for non-software related queries.

IMPORTANT: Your response MUST be a markdown block with the following format:
RESPONSE:
[Short summary of the evaluation result.]

SECURITY:
is_feature_request: true or false
confidence: 0.95
reasoning: Brief explanation focusing on why it was rejected or accepted.

- The confidence value MUST be a number between 0 and 1 (e.g., 0.95).
- Do NOT use words, phrases, or explanations in place of numbers in the confidence field.
- Do NOT include any extra text, comments, or explanations outside the markdown block.
- Do NOT use code blocks, markdown headers, or any formatting other than the above.

EXAMPLE OUTPUT:
RESPONSE:
The request is a clear software product feature requirement.

SECURITY:
is_feature_request: true
confidence: 0.98
reasoning: The request is a clear software product feature requirement.
"""

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}")
        ])
        
        self.chain = self.prompt | self.llm

    def _extract_security_from_markdown(self, text: str) -> dict:
        """Extract SECURITY section from markdown block and convert to dict."""
        # Find SECURITY section
        import re
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