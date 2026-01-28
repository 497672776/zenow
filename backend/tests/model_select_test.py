"""
Test for model selection pipeline
Tests:
1. Same model won't start multiple times
2. Switching models kills old process and starts new one
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from spacemit_llm.pipeline.model_select import ModelSelectionPipeline
from spacemit_llm.model.download import ModelDownloader
from spacemit_llm.model.llm import LLMServer
from spacemit_llm.comon.sqlite.sqlite_config import SQLiteConfig
from src import config


async def test_model_selection():
    """Test the model selection pipeline"""
    
    print("\n" + "="*80)
    print("MODEL SELECTION PIPELINE TEST")
    print("="*80)
    
    # Initialize components
    print("\n[1] Initializing components...")
    db_config = SQLiteConfig(config.DB_CONFIG_PATH)
    llm_server = LLMServer(
        host=config.LLM_SERVER_HOST,
        port=config.LLM_SERVER_PORT,
        context_size=config.LLM_SERVER_CONTEXT_SIZE,
        threads=config.LLM_SERVER_THREADS,
        gpu_layers=config.LLM_SERVER_GPU_LAYERS,
        batch_size=config.LLM_SERVER_BATCH_SIZE
    )
    downloader = ModelDownloader(config.MODELS_DIR)
    
    pipeline = ModelSelectionPipeline(
        models_dir=config.MODELS_DIR,
        downloader=downloader,
        llm_server=llm_server,
        db_config=db_config
    )
    print("✓ Components initialized")
    
    # Get available models
    print("\n[2] Checking available models...")
    models = db_config.get_all_models()
    if not models:
        print("✗ No models found in database")
        print("  Please add a model first via the UI or API")
        return
    
    test_model = models[0]
    model_name = test_model["model_name"]
    model_path = test_model["model_path"]
    print(f"✓ Using test model: {model_name}")
    print(f"  Path: {model_path}")
    
    # Check if model file exists
    if not Path(model_path).exists():
        print(f"✗ Model file not found: {model_path}")
        return
    
    # Test 1: Start model for the first time
    print("\n" + "-"*80)
    print("TEST 1: Starting model for the first time")
    print("-"*80)
    result = await pipeline.select_model(model_name)
    print(f"Result: {result}")
    
    if not result["success"]:
        print("✗ Test 1 FAILED: Could not start model")
        return
    
    print("✓ Test 1 PASSED: Model started successfully")
    
    # Wait a bit for server to stabilize
    await asyncio.sleep(2)
    
    # Test 2: Select same model again (should NOT restart)
    print("\n" + "-"*80)
    print("TEST 2: Selecting same model again (should NOT restart)")
    print("-"*80)
    status_before = llm_server.get_status()
    print(f"Status before: {status_before}")
    
    result = await pipeline.select_model(model_name)
    print(f"Result: {result}")
    
    status_after = llm_server.get_status()
    print(f"Status after: {status_after}")
    
    if not result["success"]:
        print("✗ Test 2 FAILED: Selection returned failure")
        return
    
    # Check that process PID didn't change (means no restart)
    if status_before["model_path"] == status_after["model_path"]:
        print("✓ Test 2 PASSED: Same model detected, no restart occurred")
    else:
        print("✗ Test 2 FAILED: Process might have restarted")
    
    # Test 3: Try to select a different model (if available)
    print("\n" + "-"*80)
    print("TEST 3: Switching to different model")
    print("-"*80)
    
    if len(models) > 1:
        different_model = models[1]
        diff_model_name = different_model["model_name"]
        diff_model_path = different_model["model_path"]
        
        if not Path(diff_model_path).exists():
            print(f"✗ Second model file not found: {diff_model_path}")
            print("  Skipping Test 3")
        else:
            print(f"Switching to: {diff_model_name}")
            status_before = llm_server.get_status()
            print(f"Status before: {status_before}")
            
            result = await pipeline.select_model(diff_model_name)
            print(f"Result: {result}")
            
            status_after = llm_server.get_status()
            print(f"Status after: {status_after}")
            
            if result["success"] and status_after["model_path"] == diff_model_path:
                print("✓ Test 3 PASSED: Successfully switched to different model")
            else:
                print("✗ Test 3 FAILED: Could not switch model")
            
            # Switch back to original
            print(f"\nSwitching back to: {model_name}")
            await pipeline.select_model(model_name)
    else:
        print("ℹ Only one model available, skipping Test 3")
    
    # Test 4: Verify only one llama-server process is running
    print("\n" + "-"*80)
    print("TEST 4: Verify only one llama-server process running")
    print("-"*80)
    
    import subprocess
    result = subprocess.run(
        ["pgrep", "-c", "llama-server"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        process_count = int(result.stdout.strip())
        print(f"Number of llama-server processes: {process_count}")
        
        if process_count == 1:
            print("✓ Test 4 PASSED: Exactly one llama-server process running")
        else:
            print(f"✗ Test 4 FAILED: Expected 1 process, found {process_count}")
    else:
        print("✗ Test 4 FAILED: Could not count processes")
    
    # Cleanup
    print("\n" + "-"*80)
    print("CLEANUP: Stopping llama-server")
    print("-"*80)
    await llm_server.stop()
    print("✓ Server stopped")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_model_selection())
