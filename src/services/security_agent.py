import logging
import sys
import json
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
        
        system_prompt = """You are a Security Agent responsible for evaluating whether user requests are related to software product features or general questions.

Your task is to analyze the user's input and determine if it's a feature request for a software product.

A feature request typically includes:
- Software functionality descriptions
- User interface improvements
- System enhancements
- New capabilities or tools
- Bug fixes or improvements
- Integration requirements
- Performance optimizations

General questions that are NOT feature requests include:
- Personal advice or opinions
- General knowledge questions
- Non-software related topics
- Academic questions
- Entertainment requests
- Personal problems

Respond in this exact JSON format:
{
    "is_feature_request": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of your decision"
}

Be strict but fair. When in doubt, lean towards accepting it as a feature request."""

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}")
        ])
        
        self.chain = self.prompt | self.llm

    async def evaluate_request(self, user_input: str) -> SecurityResponse:
        """
        Evaluate if the user input is a feature request.
        
        Args:
            user_input (str): The user's input text to evaluate
            
        Returns:
            SecurityResponse: Object containing the evaluation results
        """
        try:
            logger.info("Security agent evaluating request")
            result = await self.chain.ainvoke({"input": user_input})
            
            # Parse the JSON response
            response_data = json.loads(result.content)
            
            return SecurityResponse(
                is_feature_request=response_data["is_feature_request"],
                confidence=response_data["confidence"],
                reasoning=response_data["reasoning"]
            )
            
        except Exception as e:
            logger.error("Error in security agent evaluation:", exc_info=True)
            # Default to allowing the request if there's an error
            return SecurityResponse(
                is_feature_request=True,
                confidence=0.5,
                reasoning=f"Error occurred during evaluation: {str(e)}"
            ) 