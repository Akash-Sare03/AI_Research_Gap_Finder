import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

# Suppress telemetry and thread pool hangs
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["PYTHONUNBUFFERED"] = "1"

class Config:
    """Application configuration."""
    
    # Groq LLM Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen/qwen3.8-27b")
    
    # Hugging Face Embedding Configuration
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "384"))
    
    # Chunking Configuration
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "512"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    
    # Retrieval Configuration
    TOP_K: int = int(os.getenv("TOP_K", "10"))
    HYBRID_WEIGHT_SEMANTIC: float = float(os.getenv("HYBRID_WEIGHT_SEMANTIC", "0.7"))
    HYBRID_WEIGHT_KEYWORD: float = float(os.getenv("HYBRID_WEIGHT_KEYWORD", "0.3"))
    
    # Base Project Directory
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Chroma DB
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", os.path.join(BASE_DIR, "data", "vectorstore"))
    
    # Data Directory
    DATA_DIR: str = os.getenv("DATA_DIR", os.path.join(BASE_DIR, "data"))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", os.path.join(BASE_DIR, "data", "uploaded_papers"))
    
    # Authentication & Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "academic-research-gap-finder-secret-key-2026-super-secure-token")
    SESSION_EXPIRE_DAYS: int = int(os.getenv("SESSION_EXPIRE_DAYS", "7"))
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        return True