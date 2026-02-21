"""
Subconscious — Configuration
"""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Paths
    BASE_DIR: Path = Path(__file__).parent
    DATA_DIR: Path = BASE_DIR / "data"
    DB_PATH: Path = DATA_DIR / "memory.db"
    CHROMA_DIR: Path = DATA_DIR / "chroma"

    # LLM
    OLLAMA_MODEL: str = "qwen2.5-coder:7b-instruct-q4_K_M"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Memory
    STM_CAPACITY: int = 50          # Max short-term memories
    ASSOCIATION_THRESHOLD: float = 0.6  # Min similarity for association
    MAX_ASSOCIATIONS: int = 5       # Max associations to surface

    # Subconscious
    EMOTIONAL_WEIGHT_DECAY: float = 0.95  # Emotion decays over time
    MIN_INTUITION_CONFIDENCE: float = 0.4  # Min confidence to surface

    class Config:
        env_prefix = "SUBCONSCIOUS_"
        env_file = ".env"


settings = Settings()

# Ensure data directory exists
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
