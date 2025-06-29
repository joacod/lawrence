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

IMPORTANT: Your response MUST be a valid JSON object with EXACTLY these fields:
{{
    "is_feature_request": false,
    "confidence": 0.95,
    "reasoning": "Brief explanation focusing on why it was rejected or accepted"
}}

DO NOT include any other text before or after the JSON. DO NOT use code blocks, markdown, or ```json. The response must be ONLY the JSON object."""

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}")
        ])
        
        self.chain = self.prompt | self.llm

    def _extract_json_from_text(self, text: str) -> dict:
        """Extract JSON from text, handling common formatting issues."""
        # Try to find JSON-like structure in the text
        json_match = re.search(r'\{[^}]+\}', text)
        if not json_match:
            raise ValueError("No JSON object found in response")
            
        try:
            # Try to parse the matched JSON
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            # If that fails, try to clean up common formatting issues
            cleaned_text = json_match.group()
            # Replace single quotes with double quotes
            cleaned_text = cleaned_text.replace("'", '"')
            # Ensure boolean values are lowercase
            cleaned_text = cleaned_text.replace("True", "true").replace("False", "false")
            return json.loads(cleaned_text)

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
        # Only check if the request is a valid software product management request
        result = await self.chain.ainvoke({"input": user_input})
        # Try to parse the JSON response
        try:
            response_data = self._extract_json_from_text(result.content)
        except Exception as e:
            logger.error(f"Failed to parse model response: {result.content}")
            return SecurityResponse(
                is_feature_request=False,
                confidence=1.0,
                reasoning="Failed to parse security evaluation response"
            )
        # Validate required fields
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