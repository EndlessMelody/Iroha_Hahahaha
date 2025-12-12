"""
Configuration file for Anime AI Study Buddy Backend
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration."""
    
    # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Model Configuration
    MODEL_NAME = "llama-3.1-70b-versatile"
    FALLBACK_MODEL = "llama-3.1-8b-instant"
    
    # Token Limits
    MAX_CONTEXT_TOKENS = 6000
    DEFAULT_MAX_TOKENS = 800
    
    # Temperature Settings
    DEFAULT_TEMPERATURE = 0.7
    MIN_TEMPERATURE = 0.1
    MAX_TEMPERATURE = 2.0
    
    # Server Configuration
    HOST = "0.0.0.0"
    PORT = 8000
    RELOAD = True
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_ROTATION = "1 day"
    LOG_RETENTION = "7 days"
    
    # CORS
    CORS_ORIGINS = ["*"]  # Change in production
    
    # PyTorch
    TORCH_DEVICE = "cuda"  # or "cpu"
    
    # Database (for future use)
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./anime_ai.db")
    
    # Features
    ENABLE_WEBSOCKET = True
    ENABLE_SENTIMENT_ANALYSIS = True
    ENABLE_HISTORY_TRIMMING = True
    ENABLE_VOICE = True
    
    # Voice Configuration
    VOICE_PROVIDER = "groq"  # "groq" or "edge" (free)
    DEFAULT_TTS_VOICE = "Fritz-PlayAI"  # Groq PlayAI voice
    DEFAULT_STT_LANGUAGE = "ja-JP"
    TTS_SPEED = 1.05  # Speech speed
    TTS_SAMPLE_RATE = 48000  # Audio sample rate
    
    @classmethod
    def validate(cls):
        """Validate configuration."""
        if not cls.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set in environment variables")
        return True

# Validate config on import
Config.validate()
