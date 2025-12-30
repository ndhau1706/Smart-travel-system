"""
Configuration settings for the chatbot backend.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Union


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Groq Cloud Configuration - Multi API Key Support
    GROQ_API_KEYS: str = ""  # Comma-separated API keys in .env file
    GROQ_PRIMARY_MODEL: str = "llama-3.3-70b-versatile"  # Llama 3.3 70B - Main model (fast + accurate)
    GROQ_FALLBACK_MODEL: str = "llama-3.1-8b-instant"  # Llama 3.1 8B - Fast fallback
    GROQ_SECONDARY_FALLBACK_MODEL: str = "mixtral-8x7b-32768"  # Mixtral - Final backup
    
    # JWT Authentication Configuration
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production"  # CHANGE IN PRODUCTION!
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Embedding Model
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    # Database
    DATABASE_PATH: str = "./database/chatbot.db"
    
    # Cache Configuration
    CACHE_TTL: int = 300
    CACHE_MAX_SIZE: int = 1000
    
    # Search Configuration
    FAISS_INDEX_PATH: str = "./data/faiss_index"
    BM25_INDEX_PATH: str = "./data/bm25_index.pkl"
    VECTOR_DIMENSION: int = 384
    
    # Hybrid Search Weights
    # Hybrid: Semantic for understanding + BM25 for exact matching
    SEMANTIC_WEIGHT: float = 0.6
    BM25_WEIGHT: float = 0.4
    
    # Ranking Configuration
    MAX_RESULTS: int = 10  # Top results after ranking
    DISTANCE_THRESHOLD: float = 10.0
    
    # Multi-criteria Ranking Weights
    WEIGHT_RELEVANCE: float = 0.4  # Search relevance score
    WEIGHT_RATING: float = 0.25    # Restaurant rating
    WEIGHT_DISTANCE: float = 0.20  # Distance from user
    WEIGHT_POPULARITY: float = 0.15 # Rating count
    
    # Language Detection
    DEFAULT_LANGUAGE: str = "vi"
    SUPPORTED_LANGUAGES: str = "vi,en"
    
    # Data Source
    RESTAURANTS_JSON_PATH: str = "./hcm_restaurants_chatbot.json"
    
    @property
    def supported_languages_list(self) -> List[str]:
        """Get supported languages as a list"""
        return [lang.strip() for lang in self.SUPPORTED_LANGUAGES.split(',')]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra='ignore'
    )


settings = Settings()
