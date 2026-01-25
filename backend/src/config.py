"""
Default configuration management for Zenow backend
"""
from pathlib import Path

# Base directories
BASE_DIR = Path.home() / ".cache" / "zenow"
DATA_DIR = BASE_DIR / "data"
DB_DIR = DATA_DIR / "db"
MODELS_DIR = BASE_DIR / "model"  # Changed from data/models to model

# Ensure directories exist
BASE_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

# Database configuration
DB_CONFIG_PATH = DB_DIR / "config.db"

# LLM Server default configuration
LLM_SERVER_HOST = "127.0.0.1"
LLM_SERVER_PORT = 8051
LLM_SERVER_CONTEXT_SIZE = 15360
LLM_SERVER_THREADS = 8
LLM_SERVER_GPU_LAYERS = 0
LLM_SERVER_BATCH_SIZE = 512
LLM_SERVER_NO_MMAP = True
LLM_SERVER_METRICS = True

# API Server configuration
API_SERVER_HOST = "0.0.0.0"
API_SERVER_PORT = 8050

# LLM Client default configuration
LLM_CLIENT_BASE_URL = f"http://{LLM_SERVER_HOST}:{LLM_SERVER_PORT}/v1"
LLM_CLIENT_TEMPERATURE = 0.7
LLM_CLIENT_REPEAT_PENALTY = 1.1
LLM_CLIENT_MAX_TOKENS = 2048

# Default model configuration
DEFAULT_MODEL_NAME = "qwen3"
DEFAULT_MODEL_PATH = ""  # To be set by user

# Default model download URLs
DEFAULT_MODEL_DOWNLOAD_URLS = [
    "https://modelscope.cn/models/second-state/Qwen2.5-0.5B-Instruct-GGUF/resolve/master/Qwen2.5-0.5B-Instruct-Q4_0.gguf",
    "https://modelscope.cn/models/unsloth/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q4_K_M.gguf"
]

# Default file browser path for model selection
DEFAULT_MODEL_BROWSER_PATH = str(Path.home() / "Downloads" / "models")
