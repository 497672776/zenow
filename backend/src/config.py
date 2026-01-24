"""
Default configuration management for Zenow backend
"""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = DATA_DIR / "db"
MODELS_DIR = DATA_DIR / "models"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

# Database configuration
DATABASE_PATH = DB_DIR / "zenow.db"
DB_CONFIG_PATH = DB_DIR / "config.db"

# LLM Server default configuration
LLM_SERVER_HOST = "127.0.0.1"
LLM_SERVER_PORT = 8080
LLM_SERVER_CONTEXT_SIZE = 15360
LLM_SERVER_THREADS = 8
LLM_SERVER_GPU_LAYERS = 0
LLM_SERVER_BATCH_SIZE = 512
LLM_SERVER_NO_MMAP = True
LLM_SERVER_METRICS = True

# LLM Client default configuration
LLM_CLIENT_BASE_URL = f"http://{LLM_SERVER_HOST}:{LLM_SERVER_PORT}/v1"
LLM_CLIENT_TEMPERATURE = 0.7
LLM_CLIENT_REPEAT_PENALTY = 1.1
LLM_CLIENT_MAX_TOKENS = 2048

# Default model configuration
DEFAULT_MODEL_NAME = "qwen3"
DEFAULT_MODEL_PATH = ""  # To be set by user

# Model status
MODEL_STATUS_NOT_STARTED = "not_started"
MODEL_STATUS_STARTING = "starting"
MODEL_STATUS_RUNNING = "running"
MODEL_STATUS_ERROR = "error"
MODEL_STATUS_STOPPED = "stopped"
