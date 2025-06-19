class Settings:
    # Application Settings
    APP_NAME: str = "AI Product Owner Agent"
    
    # Model Settings
    PO_MODEL: str = "llama3:latest"
    SECURITY_MODEL: str = "llama3:latest"
    MAX_HISTORY_LENGTH: int = 20

settings = Settings() 