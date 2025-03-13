# config.py
import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Configurações da aplicação."""
    
    # Aplicação
    APP_NAME: str = "Financial Tracker"
    DEBUG: bool = os.environ.get("DEBUG", "False") == "True"
    
    # MongoDB
    MONGODB_URI: str = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
    MONGODB_HOST: str = os.environ.get("MONGODB_HOST", "localhost")
    MONGODB_PORT: int = int(os.environ.get("MONGODB_PORT", "27017"))
    MONGODB_DB: str = os.environ.get("MONGODB_DB", "financial_tracker")
    MONGODB_USERNAME: str = os.environ.get("MONGODB_USERNAME", "")
    MONGODB_PASSWORD: str = os.environ.get("MONGODB_PASSWORD", "")
   
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")    
    USE_LLM_FALLBACK: bool = os.environ.get("USE_LLM_FALLBACK", "False") == "True"
    
    # Servidor
    HOST: str = os.environ.get("HOST", "0.0.0.0")
    PORT: int = int(os.environ.get("PORT", "8000"))
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()