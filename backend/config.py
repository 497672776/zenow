"""
Default configuration management for Zenow backend
"""
from pathlib import Path

# Base directories
BASE_DIR = Path.home() / ".cache" / "zenow"
DATA_DIR = BASE_DIR / "data"
DB_DIR = DATA_DIR / "db"
MODELS_DIR = BASE_DIR / "models"  # Changed to plural for multi-model support

# Model directories by mode
LLM_MODELS_DIR = MODELS_DIR / "llm"
EMBED_MODELS_DIR = MODELS_DIR / "embed"
RERANK_MODELS_DIR = MODELS_DIR / "rerank"

# Ensure directories exist
BASE_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)
LLM_MODELS_DIR.mkdir(exist_ok=True)
EMBED_MODELS_DIR.mkdir(exist_ok=True)
RERANK_MODELS_DIR.mkdir(exist_ok=True)

# Database configuration
DB_CONFIG_PATH = DB_DIR / "config.db"
DB_SESSION_PATH = DB_DIR / "sessions.db"  # 会话历史数据库

# LLM Server default configuration
LLM_SERVER_HOST = "127.0.0.1"
LLM_SERVER_PORT = 8051  # LLM 模式端口
EMBED_SERVER_PORT = 8052  # Embed 模式端口
RERANK_SERVER_PORT = 8053  # Rerank 模式端口
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

# System prompt configuration
DEFAULT_SYSTEM_PROMPT = """你是一个有帮助的AI助手。请用简洁、准确的方式回答用户的问题。"""

# Default model configuration
DEFAULT_MODEL_NAME = "qwen3"
DEFAULT_MODEL_PATH = ""  # To be set by user

# Default model download URLs by mode
DEFAULT_MODEL_DOWNLOAD_URLS = {
    "llm": [
        "https://modelscope.cn/models/second-state/Qwen2.5-0.5B-Instruct-GGUF/resolve/master/Qwen2.5-0.5B-Instruct-Q4_0.gguf",
        "https://modelscope.cn/models/unsloth/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q4_K_M.gguf"
    ],
    "embed": [
        "https://hf-mirror.com/nomic-ai/nomic-embed-text-v2-moe-GGUF/resolve/main/nomic-embed-text-v2-moe.Q4_0.gguf"
    ],
    "rerank": [
        "https://modelscope.cn/models/gpustack/bge-reranker-v2-m3-GGUF/resolve/master/bge-reranker-v2-m3-Q4_0.gguf"
    ]
}

# Default file browser path for model selection
DEFAULT_MODEL_BROWSER_PATH = str(Path.home() / "Downloads" / "models")

# Helper function to get model directory by mode
def get_model_dir(mode: str = "llm") -> Path:
    """
    Get the model directory for a specific mode

    Args:
        mode: Model mode ('llm', 'embed', 'rerank')

    Returns:
        Path to the model directory
    """
    if mode == "llm":
        return LLM_MODELS_DIR
    elif mode == "embed":
        return EMBED_MODELS_DIR
    elif mode == "rerank":
        return RERANK_MODELS_DIR
    else:
        raise ValueError(f"Invalid model mode: {mode}. Must be 'llm', 'embed', or 'rerank'")
