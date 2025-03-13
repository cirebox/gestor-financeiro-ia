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
   
    # NLP e OpenAI
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")    
    USE_LLM_FALLBACK: bool = os.environ.get("USE_LLM_FALLBACK", "False") == "True"

    # WhatsApp Integration
    WHATSAPP_API_KEY: str = os.environ.get("WHATSAPP_API_KEY", "whatsapp-integration-secret-key")
    
    # Servidor
    HOST: str = os.environ.get("HOST", "0.0.0.0")
    PORT: int = int(os.environ.get("PORT", "8000"))
    BASE_URL: str = os.environ.get("BASE_URL", f"http://localhost:{PORT}")
    
    # JWT e Segurança
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "changeme_in_production_this_is_insecure")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.environ.get("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60"))
    
    # SMTP para envio de emails
    SMTP_SERVER: str = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.environ.get("SMTP_PASSWORD", "")
    SENDER_EMAIL: str = os.environ.get("SENDER_EMAIL", "noreply@financialtracker.com")
    SENDER_NAME: str = os.environ.get("SENDER_NAME", "Financial Tracker")    
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()