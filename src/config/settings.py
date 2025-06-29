class Settings:
    # Application Settings
    APP_NAME: str = "AI Product Owner Agent"
    MAX_HISTORY_LENGTH: int = 20
    
    # Model Settings
    SECURITY_MODEL: str = "phi3:latest" # Lightweight, fast model for classifying requests.
    PO_MODEL: str = "mistral:latest" # Advanced 7B model with enhanced reasoning.
    CONTEXT_MODEL: str = "phi3:latest" # Model for context validation agent.
    QUESTION_ANALYSIS_MODEL: str = "phi3:latest" # Model for question analysis agent.

settings = Settings() 