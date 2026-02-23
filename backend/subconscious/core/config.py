"""
Subconscious — Configuration

Merkezi yapılandırma. Ortam değişkenleriyle override edilebilir.
"""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Paths
    BASE_DIR: Path = Path.cwd()
    DATA_DIR: Path = BASE_DIR / "mind_data"

    # Memory
    WORKING_MEMORY_CAPACITY: int = 7    # Miller's Law: 7±2
    EPISODIC_CAPACITY: int = 500        # Max episodic memories before pruning
    MIN_SIMILARITY: float = 0.5         # Min vector similarity for recall

    # Cognitive Graph
    ACTIVATION_DECAY: float = 0.1       # Activation decay rate per cycle
    SPREAD_FACTOR: float = 0.6          # Spreading activation propagation factor
    MIN_ASSOCIATION_WEIGHT: float = 0.1  # Below this, edges are pruned

    # Creative Engine
    CREATIVITY_TEMPERATURE: float = 0.8  # LLM temperature for creative ops
    MIN_NOVELTY_SCORE: float = 0.3      # Min novelty to surface a creative spark

    # Background Processor
    DREAM_INTERVAL: int = 300           # Seconds between dream cycles
    CONSOLIDATION_INTERVAL: int = 300   # Seconds between consolidation
    FORGETTING_THRESHOLD: float = 0.2   # Below this importance, forget

    # LLM (defaults; adapter-level override)
    DEFAULT_MODEL: str = "llama3.1:8b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    class Config:
        env_prefix = "SUBCONSCIOUS_"
        env_file = ".env"


settings = Settings()

# Ensure data directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
