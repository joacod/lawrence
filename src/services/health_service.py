from langchain_ollama.chat_models import ChatOllama
from src.config.settings import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class HealthService:
    def __init__(self):
        self.ollama_client = ChatOllama(model=settings.PO_MODEL)
    
    async def check_health(self) -> dict:
        """
        Simple health check that tests Ollama connectivity
        Returns: {"status": "healthy|unhealthy", "message": "descriptive message"}
        """
        try:
            logger.info("Checking Ollama connectivity...")
            
            # Try a simple completion to test connectivity
            await self.ollama_client.ainvoke("ping")
            
            logger.info("Ollama check successful")
            return {
                "status": "healthy",
                "message": "Service up and running"
            }
            
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": "Ollama connection failed"
            } 