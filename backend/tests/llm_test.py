# -*- coding: utf-8 -*-
"""
Test file for LLM functionality
Tests LLM server and client with actual models from /home/liudecheng/Downloads/models/
"""
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from spacemit_llm.model.llm import LLMServer, LLMClient
from spacemit_llm.comon.sqlite.sqlite_config import SQLiteConfig
from config import DB_CONFIG_PATH

# Model paths
MODEL_DIR = Path("/home/liudecheng/Downloads/models")
MODEL1_PATH = MODEL_DIR / "Qwen2.5-0.5B-Instruct-Q4_0.gguf"
MODEL2_PATH = MODEL_DIR / "Qwen3-0.6B-Q4_K_M.gguf"
MODEL1_NAME = "Qwen2.5-0.5B-Instruct"
MODEL2_NAME = "Qwen3-0.6B"


def print_section(title: str):
    """Print a section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_database_config():
    """Test database configuration"""
    print_section("Testing Database Configuration")

    db = SQLiteConfig(DB_CONFIG_PATH)

    # Add models to database
    print(f"Adding model 1: {MODEL1_NAME}")
    model1_id = db.add_model(MODEL1_NAME, str(MODEL1_PATH))
    print(f"  Model 1 ID: {model1_id}")

    print(f"Adding model 2: {MODEL2_NAME}")
    model2_id = db.add_model(MODEL2_NAME, str(MODEL2_PATH))
    print(f"  Model 2 ID: {model2_id}")

    # Get all models
    all_models = db.get_all_models()
    print(f"\nAll models in database: {len(all_models)}")
    for model in all_models:
        print(f"  - {model['model_name']}: {model['model_path']}")

    # Set model 1 as current
    print(f"\nSetting {MODEL1_NAME} as current model")
    try:
        db.set_current_model(model1_id)
        current = db.get_current_model()
        print(f"Current model: {current['model_name']}")
    except ValueError as e:
        print(f"Error setting current model: {e}")
        print("This is expected if the model file doesn't exist")

    # Test parameters
    print("\nTesting parameter storage")
    db.set_parameter("temperature", 0.7, "float")
    db.set_parameter("repeat_penalty", 1.1, "float")
    db.set_parameter("max_tokens", 2048, "int")

    params = db.get_all_parameters()
    print(f"Stored parameters: {params}")

    print("\n Database configuration test passed!")
    return db, model1_id, model2_id


def test_llm_server_start_stop(model_path: str, model_name: str):
    """Test LLM server start and stop"""
    print_section(f"Testing LLM Server Start/Stop with {model_name}")

    server = LLMServer(
        host="127.0.0.1",
        port=8080,
        context_size=4096,  # Smaller context for faster startup
        threads=4,
        gpu_layers=0,
        batch_size=512
    )

    # Check initial status
    status = server.get_status()
    print(f"Initial status: {status['status']}")

    # Start server
    print(f"\nStarting server with model: {model_name}")
    print(f"Model path: {model_path}")
    success = server.start_server(str(model_path), model_name)

    if success:
        print(" Server started successfully!")
        status = server.get_status()
        print(f"Server status: {status}")

        # Wait a bit to ensure server is ready
        time.sleep(2)

        # Stop server
        print("\nStopping server...")
        server.stop_server()
        status = server.get_status()
        print(f"Server status after stop: {status['status']}")
        print(" Server stopped successfully!")
        return True
    else:
        print(f"L Failed to start server: {server.error_message}")
        return False


def test_llm_model_switch():
    """Test switching between models"""
    print_section("Testing Model Switching")

    server = LLMServer(
        context_size=4096,
        threads=4
    )

    # Start with model 1
    print(f"Starting with {MODEL1_NAME}...")
    success = server.start_server(str(MODEL1_PATH), MODEL1_NAME)
    if not success:
        print(f"L Failed to start model 1: {server.error_message}")
        return False

    print(f" {MODEL1_NAME} started")
    status = server.get_status()
    print(f"Current model: {status['model_name']}")

    time.sleep(2)

    # Switch to model 2
    print(f"\nSwitching to {MODEL2_NAME}...")
    success = server.switch_model(str(MODEL2_PATH), MODEL2_NAME)
    if not success:
        print(f"L Failed to switch to model 2: {server.error_message}")
        server.stop_server()
        return False

    print(f" Switched to {MODEL2_NAME}")
    status = server.get_status()
    print(f"Current model: {status['model_name']}")

    # Clean up
    print("\nCleaning up...")
    server.stop_server()
    print(" Model switching test passed!")
    return True


def test_llm_client_chat(model_path: str, model_name: str):
    """Test LLM client chat functionality"""
    print_section(f"Testing LLM Client Chat with {model_name}")

    # Start server
    server = LLMServer(context_size=4096, threads=4)
    print(f"Starting server with {model_name}...")
    success = server.start_server(str(model_path), model_name)

    if not success:
        print(f"L Failed to start server: {server.error_message}")
        return False

    print(" Server started")

    try:
        # Create client
        client = LLMClient(
            base_url="http://127.0.0.1:8080/v1",
            temperature=0.7,
            repeat_penalty=1.1,
            max_tokens=100
        )

        # Test non-streaming chat
        print("\n--- Testing Non-Streaming Chat ---")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2? Answer briefly."}
        ]

        print("Sending messages:")
        for msg in messages:
            print(f"  {msg['role']}: {msg['content']}")

        print("\nWaiting for response...")
        response = client.chat_completion(messages, stream=False)

        print("\nResponse received:")
        print(f"  {response}")

        if 'choices' in response and len(response['choices']) > 0:
            assistant_message = response['choices'][0]['message']['content']
            print(f"\nAssistant: {assistant_message}")
            print(" Non-streaming chat test passed!")
        else:
            print("L Unexpected response format")
            return False

    except Exception as e:
        print(f"L Chat test failed: {str(e)}")
        return False
    finally:
        # Clean up
        print("\nStopping server...")
        server.stop_server()
        print(" Server stopped")

    return True


def test_llm_client_stream(model_path: str, model_name: str):
    """Test LLM client streaming functionality"""
    print_section(f"Testing LLM Client Streaming with {model_name}")

    # Start server
    server = LLMServer(context_size=4096, threads=4)
    print(f"Starting server with {model_name}...")
    success = server.start_server(str(model_path), model_name)

    if not success:
        print(f"L Failed to start server: {server.error_message}")
        return False

    print(" Server started")

    try:
        # Create client
        client = LLMClient(
            base_url="http://127.0.0.1:8080/v1",
            temperature=0.7,
            repeat_penalty=1.1,
            max_tokens=100
        )

        # Test streaming chat
        print("\n--- Testing Streaming Chat ---")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Count from 1 to 5."}
        ]

        print("Sending messages:")
        for msg in messages:
            print(f"  {msg['role']}: {msg['content']}")

        print("\nStreaming response:")
        print("Assistant: ", end="", flush=True)

        full_response = ""
        chunk_count = 0

        for chunk in client.chat_completion(messages, stream=True):
            if 'choices' in chunk and len(chunk['choices']) > 0:
                delta = chunk['choices'][0].get('delta', {})
                if 'content' in delta and delta['content'] is not None:
                    content = delta['content']
                    print(content, end="", flush=True)
                    full_response += content
                    chunk_count += 1

        print()  # New line after streaming
        print(f"\nReceived {chunk_count} chunks")
        print(f"Full response: {full_response}")
        print(" Streaming chat test passed!")

    except Exception as e:
        print(f"L Streaming test failed: {str(e)}")
        return False
    finally:
        # Clean up
        print("\nStopping server...")
        server.stop_server()
        print(" Server stopped")

    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  LLM Functionality Test Suite")
    print("=" * 60)
    print(f"\nModel 1: {MODEL1_NAME}")
    print(f"  Path: {MODEL1_PATH}")
    print(f"Model 2: {MODEL2_NAME}")
    print(f"  Path: {MODEL2_PATH}")

    # Verify models exist
    if not MODEL1_PATH.exists():
        print(f"\nL ERROR: Model 1 not found at {MODEL1_PATH}")
        return
    if not MODEL2_PATH.exists():
        print(f"\nL ERROR: Model 2 not found at {MODEL2_PATH}")
        return

    results = []

    # Test 1: Database configuration
    try:
        db, model1_id, model2_id = test_database_config()
        results.append(("Database Configuration", True))
    except Exception as e:
        print(f"\nL Database test failed: {str(e)}")
        results.append(("Database Configuration", False))
        return

    # Test 2: Server start/stop with model 1
    try:
        success = test_llm_server_start_stop(MODEL1_PATH, MODEL1_NAME)
        results.append((f"Server Start/Stop ({MODEL1_NAME})", success))
    except Exception as e:
        print(f"\nL Server start/stop test failed: {str(e)}")
        results.append((f"Server Start/Stop ({MODEL1_NAME})", False))

    # Test 3: Model switching
    try:
        success = test_llm_model_switch()
        results.append(("Model Switching", success))
    except Exception as e:
        print(f"\nL Model switching test failed: {str(e)}")
        results.append(("Model Switching", False))

    # Test 4: Client chat (non-streaming)
    try:
        success = test_llm_client_chat(MODEL1_PATH, MODEL1_NAME)
        results.append(("Client Chat (Non-Streaming)", success))
    except Exception as e:
        print(f"\nL Client chat test failed: {str(e)}")
        results.append(("Client Chat (Non-Streaming)", False))

    # Test 5: Client streaming
    try:
        success = test_llm_client_stream(MODEL1_PATH, MODEL1_NAME)
        results.append(("Client Chat (Streaming)", success))
    except Exception as e:
        print(f"\nL Client streaming test failed: {str(e)}")
        results.append(("Client Chat (Streaming)", False))

    # Print summary
    print_section("Test Summary")
    passed = 0
    failed = 0
    for test_name, success in results:
        status = " PASSED" if success else "L FAILED"
        print(f"{test_name:<40} {status}")
        if success:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\n<� All tests passed!")
    else:
        print(f"\n�  {failed} test(s) failed")


if __name__ == "__main__":
    run_all_tests()
