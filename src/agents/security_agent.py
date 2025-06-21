import logging
import sys
import json
import re
from typing import Optional, Dict, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.chat_models import ChatOllama
from src.config.settings import settings
from src.models.agent_response import SecurityResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SecurityAgent:
    def __init__(self):
        """Initialize the Security Agent with the LLM model and prompt template."""
        self.llm = ChatOllama(model=settings.SECURITY_MODEL)
        
        system_prompt = """You are a strict Security Agent for a Software Product Management Enhancement System. Your primary responsibility is to evaluate requests for relevance to software product management, development, or company operations.

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

CONTEXT-AWARE EVALUATION:
- If this is a follow-up request to an existing feature, evaluate it in the context of the original feature
- Follow-up requests that expand, clarify, or add details to the original feature should be ACCEPTED
- Consider the original feature's domain and accept related technical specifications, requirements, or enhancements
- Examples of valid follow-ups:
  * Original: "login system" → Follow-up: "password strength validation" (ACCEPT)
  * Original: "login system" → Follow-up: "two-factor authentication" (ACCEPT)
  * Original: "login system" → Follow-up: "password reset functionality" (ACCEPT)
  * Original: "user dashboard" → Follow-up: "add charts and graphs" (ACCEPT)
  * Original: "user dashboard" → Follow-up: "real-time data updates" (ACCEPT)
  * Original: "payment system" → Follow-up: "support for multiple currencies" (ACCEPT)
  * Original: "payment system" → Follow-up: "payment gateway integration" (ACCEPT)
  * Original: "notification system" → Follow-up: "email and SMS notifications" (ACCEPT)
  * Original: "notification system" → Follow-up: "push notifications" (ACCEPT)
  * Original: "user profile" → Follow-up: "profile picture upload" (ACCEPT)
  * Original: "search functionality" → Follow-up: "advanced filters" (ACCEPT)
  * Original: "reporting system" → Follow-up: "export to PDF" (ACCEPT)

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
1. When in doubt, REJECT the request
2. The request must EXPLICITLY mention software, product, development, or technical aspects
3. Reject vague requests that could be interpreted as non-software related
4. Require clear software product management context
5. Zero tolerance for non-software related queries
6. Consider the original feature context when evaluating follow-ups
7. Accept technical specifications, requirements, and enhancements related to the original feature

IMPORTANT: Your response MUST be a valid JSON object with EXACTLY these fields:
{{
    "is_feature_request": false,
    "confidence": 0.95,
    "reasoning": "Brief explanation focusing on why it was rejected or accepted"
}}

DO NOT include any other text before or after the JSON. The response must be ONLY the JSON object."""

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
            session_context (Optional[Dict]): Context about the current session including original feature title
            
        Returns:
            SecurityResponse: Object containing the evaluation results
        """
        logger.info("Security agent evaluating request")
        
        # Prepare the input with context if available
        if session_context and session_context.get('title'):
            original_feature = session_context['title']
            contextual_input = f"""CONTEXT: This is a follow-up request to an existing feature.

ORIGINAL FEATURE: {original_feature}

CURRENT REQUEST: {user_input}

Please evaluate if the current request is related to or enhances the original feature."""
            logger.info(f"Evaluating with context - Original: {original_feature}")
        else:
            contextual_input = user_input
            logger.info("Evaluating without context")
        
        result = await self.chain.ainvoke({"input": contextual_input})
        
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