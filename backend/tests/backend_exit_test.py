"""
Test backend exit handler
Verifies that llama-server is cleaned up when backend exits
"""

import sys
import time
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from spacemit_llm.model.llm import LLMServer
from spacemit_llm.pipeline.backend_exit import BackendExitHandler
from src import config


def test_exit_handler():
    """Test that exit handler cleans up llama-server"""
    
    print("\n" + "="*80)
    print("BACKEND EXIT HANDLER TEST")
    print("="*80)
    
    # Initialize LLM server
    print("\n[1] Initializing LLM server...")
    llm_server = LLMServer(
        host=config.LLM_SERVER_HOST,
        port=config.LLM_SERVER_PORT,
        context_size=config.LLM_SERVER_CONTEXT_SIZE,
        threads=config.LLM_SERVER_THREADS,
        gpu_layers=config.LLM_SERVER_GPU_LAYERS,
        batch_size=config.LLM_SERVER_BATCH_SIZE
    )
    print("✓ LLM server initialized")
    
    # Get a test model from database
    print("\n[2] Getting test model...")
    from spacemit_llm.comon.sqlite.sqlite_config import SQLiteConfig
    db_config = SQLiteConfig(config.DB_CONFIG_PATH)
    models = db_config.get_all_models()
    
    if not models:
        print("✗ No models found in database")
        return
    
    test_model = models[0]
    model_path = test_model["model_path"]
    model_name = test_model["model_name"]
    
    if not Path(model_path).exists():
        print(f"✗ Model file not found: {model_path}")
        return
    
    print(f"✓ Using model: {model_name}")
    
    # Start the server
    print("\n[3] Starting llama-server...")
    success = llm_server.start_server(model_path, model_name)
    
    if not success:
        print("✗ Failed to start llama-server")
        return
    
    print("✓ llama-server started")
    
    # Verify process is running
    time.sleep(2)
    result = subprocess.run(
        ["pgrep", "-c", "llama-server"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        process_count = int(result.stdout.strip())
        print(f"✓ llama-server processes before cleanup: {process_count}")
    else:
        print("✗ Could not verify llama-server process")
        return
    
    # Register and trigger exit handler
    print("\n[4] Registering exit handler...")
    exit_handler = BackendExitHandler(llm_server)
    exit_handler.register()
    print("✓ Exit handler registered")
    
    print("\n[5] Triggering cleanup...")
    exit_handler._cleanup()
    
    # Wait a bit for process to terminate
    time.sleep(2)
    
    # Verify process is stopped
    print("\n[6] Verifying cleanup...")
    result = subprocess.run(
        ["pgrep", "-c", "llama-server"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("✓ All llama-server processes cleaned up successfully")
    else:
        process_count = int(result.stdout.strip())
        print(f"✗ Still {process_count} llama-server process(es) running")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    test_exit_handler()
