import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "emergency.db"
DOCUMENTS_DIR = DATA_DIR / "documents"

# Ollama local inference endpoint (no cloud access required)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:mini")  # or llama3.2:3b

# Retrieval and ranking limits
RETRIEVAL_LIMIT = 3
BM25_RELEVANCE_THRESHOLD = -15.0  # FTS5 BM25 returns negative values (lower is more relevant)
