import logging
import sys
import asyncio
from langchain_ollama.chat_models import ChatOllama
from src.config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class HealthService:
    def __init__(self):
        self.ollama_client = ChatOllama(model=settings.PO_MODEL)
    
    async def check_health(self) -> dict:
        """
        Simple health check that tests Ollama connectivity
        Returns: {"status": "healthy|unhealthy", "service": "app_name"}
        """
        try:
            logger.info("Checking Ollama connectivity...")
            
            # Try a simple completion to test connectivity
            await self.ollama_client.ainvoke("ping")
            
            logger.info("Ollama check successful")
            return {
                "status": "healthy",
                "service": settings.APP_NAME
            }
            
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": settings.APP_NAME
            } 