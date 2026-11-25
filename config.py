"""
config.py - Central Configuration for AnticipateCart
Configurable parameters for threshold tuning, search limits, and API keys.
"""
import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class AppConfig(BaseModel):
    # Anticipatory Policy Parameters
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.85"))
    WASTED_SEARCH_LIMIT_PER_REQUEST: int = int(os.getenv("WASTED_SEARCH_LIMIT_PER_REQUEST", "3"))
    MIN_SCORE_GAP: float = float(os.getenv("MIN_SCORE_GAP", "0.35"))
    MIN_STABLE_TOKENS: int = int(os.getenv("MIN_STABLE_TOKENS", "1"))
    
    # Rezolve Labs Integration
    REZOLVE_API_KEY: str = os.getenv("REZOLVE_API_KEY", "rezolve_coupon_demo_2026")
    REZOLVE_BASE_URL: str = os.getenv("REZOLVE_BASE_URL", "https://api.rezolvelabs.ai/v1")
    REZOLVE_ENABLED: bool = os.getenv("REZOLVE_ENABLED", "true").lower() in ("true", "1", "yes")
    REZOLVE_TIMEOUT_SEC: float = 2.0
    
    # Gemini / Vision API
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Database
    DATABASE_PATH: str = os.path.join(os.path.dirname(__file__), "anticipatecart.db")
    
    # App Settings
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1")
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))

config = AppConfig()
