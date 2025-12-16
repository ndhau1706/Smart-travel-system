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
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    
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
    # BM25 ONLY - semantic search causes incorrect results
    SEMANTIC_WEIGHT: float = 0.0
    BM25_WEIGHT: float = 1.0
    
    # Ranking Configuration
    MAX_RESULTS: int = 10  # Always return 10 results
    DISTANCE_THRESHOLD: float = 10.0
    
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
