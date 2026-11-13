"""Application configuration settings."""

import os
from pathlib import Path

# Resolve base directories
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

# Database path (can be overridden via FLYNGO_DB env var, e.g. for testing)
DEFAULT_DB_PATH = str(BACKEND_DIR / "flyngo.db")
DB_PATH = os.getenv("FLYNGO_DB", DEFAULT_DB_PATH)

# Data directory containing JSON catalogs and problem data
DATA_DIR = Path(os.getenv("FLYNGO_DATA_DIR", str(ROOT_DIR / "data")))

# Log file (rotated). The directory is gitignored.
# Vercel can write only under /tmp.
DEFAULT_LOG_PATH = (
    "/tmp/flyngo.log" if os.getenv("VERCEL") else str(BACKEND_DIR / "logs" / "flyngo.log")
)
LOG_PATH = os.getenv("FLYNGO_LOG_PATH", DEFAULT_LOG_PATH)

# CORS origins
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
