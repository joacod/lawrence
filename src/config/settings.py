class Settings:
    # Application Settings
    APP_NAME: str = "AI Product Owner Agent"
    MAX_HISTORY_LENGTH: int = 20
    
    # Model Settings
    SECURITY_MODEL: str = "phi3:latest"
    PO_MODEL: str = "llama3:latest"

settings = Settings() 