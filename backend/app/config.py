import os
from pydantic import BaseModel

class Settings(BaseModel):
    SECRET_KEY: str = os.getenv("SECRET_KEY", "finnk_super_secret_jwt_key_2026_financial_platform")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./finnk.db")
    
    # Configurações do Provedor de IA (Google Gemini API - Free Tier)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "gemini")
    AI_MAX_OUTPUT_TOKENS: int = int(os.getenv("AI_MAX_OUTPUT_TOKENS", "800"))
    AI_TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.3"))

settings = Settings()
