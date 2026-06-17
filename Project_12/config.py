"""
Central configuration for Project_12.
All paths resolve relative to PROJECT12_BASE_DIR unless overridden by env vars.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Base directory — anchor for all relative paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(os.getenv("PROJECT12_BASE_DIR", Path(__file__).parent.resolve())).resolve()

# ---------------------------------------------------------------------------
# Data paths
# ---------------------------------------------------------------------------
DATA_DIR = Path(os.getenv("PROJECT12_DATA_DIR", BASE_DIR / "data")).resolve()
VECTORSTORE_DIR = Path(os.getenv("PROJECT12_VECTORSTORE_DIR", BASE_DIR / "vectorstore")).resolve()
MEMORY_DATA_DIR = Path(os.getenv("PROJECT12_MEMORY_DATA_DIR", BASE_DIR / "memory_data")).resolve()

PROFILE_FILE = MEMORY_DATA_DIR / "profiles.json"
CHAT_FILE = MEMORY_DATA_DIR / "chats.json"
SESSION_FILE = MEMORY_DATA_DIR / "sessions.json"
QA_FILE = MEMORY_DATA_DIR / "qa_logs.json"

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------
EMBEDDING_MODEL = os.getenv("PROJECT12_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
RERANKER_MODEL = os.getenv("PROJECT12_RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
CHUNK_SIZE = int(os.getenv("PROJECT12_CHUNK_SIZE", "1200"))
CHUNK_OVERLAP = int(os.getenv("PROJECT12_CHUNK_OVERLAP", "200"))
MODEL = os.getenv("PROJECT12_LLM_MODEL", "openrouter/free")

# ---------------------------------------------------------------------------
# Service configuration
# ---------------------------------------------------------------------------
SERVICE_HOST = os.getenv("PROJECT12_HOST", "0.0.0.0")
SERVICE_PORT = int(os.getenv("PROJECT12_PORT", "8100"))
LOG_LEVEL = os.getenv("PROJECT12_LOG_LEVEL", "INFO").upper()

# ---------------------------------------------------------------------------
# Operational flags
# ---------------------------------------------------------------------------
AUTO_INGEST = os.getenv("PROJECT12_AUTO_INGEST", "false").lower() in ("true", "1", "yes")
LLM_TIMEOUT_SECONDS = int(os.getenv("PROJECT12_LLM_TIMEOUT_SECONDS", "30"))
RETRIEVAL_TOP_K = int(os.getenv("PROJECT12_RETRIEVAL_TOP_K", "7"))
RETRIEVAL_CANDIDATE_K = int(os.getenv("PROJECT12_RETRIEVAL_CANDIDATE_K", "20"))

# ---------------------------------------------------------------------------
# External API
# ---------------------------------------------------------------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
API_KEY = os.getenv("PROJECT12_API_KEY", "")
AUTH_ENABLED = os.getenv("PROJECT12_AUTH_ENABLED", "true").lower() in ("true", "1", "yes")

# Paths exempt from authentication (k8s probes only)
PUBLIC_PATHS = frozenset({"/health", "/ready"})

MAX_REQUEST_BODY_BYTES = int(os.getenv("PROJECT12_MAX_REQUEST_BYTES", "65536"))

# Per-IP rate limits (requests per window)
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("PROJECT12_RATE_LIMIT_WINDOW", "60"))
RATE_LIMIT_CHAT = int(os.getenv("PROJECT12_RATE_LIMIT_CHAT", "20"))
RATE_LIMIT_CRISIS = int(os.getenv("PROJECT12_RATE_LIMIT_CRISIS", "40"))
RATE_LIMIT_MEMORY = int(os.getenv("PROJECT12_RATE_LIMIT_MEMORY", "60"))

# Abuse protection: max identical POST bodies per IP within dedup window
ABUSE_DEDUP_WINDOW_SECONDS = int(os.getenv("PROJECT12_ABUSE_DEDUP_WINDOW", "10"))
ABUSE_MAX_IDENTICAL_REQUESTS = int(os.getenv("PROJECT12_ABUSE_MAX_IDENTICAL", "5"))
