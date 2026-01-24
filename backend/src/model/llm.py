"""
LLM Server and Client implementation for Zenow backend
"""
import subprocess
import os
import signal
import time
import requests
from typing import Optional, Dict, Any, List, Iterator
from pathlib import Path
import logging
from ..config import (
    LLM_SERVER_HOST, LLM_SERVER_PORT, LLM_SERVER_CONTEXT_SIZE,
    LLM_SERVER_THREADS, LLM_SERVER_GPU_LAYERS, LLM_SERVER_BATCH_SIZE,
    LLM_CLIENT_BASE_URL, LLM_CLIENT_TEMPERATURE, LLM_CLIENT_REPEAT_PENALTY,
    LLM_CLIENT_MAX_TOKENS, MODEL_STATUS_NOT_STARTED, MODEL_STATUS_STARTING,
    MODEL_STATUS_RUNNING, MODEL_STATUS_ERROR, MODEL_STATUS_STOPPED
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMServer:
    """LLM Server management class"""

    def __init__(
        self,
        host: str = LLM_SERVER_HOST,
        port: int = LLM_SERVER_PORT,
        context_size: int = LLM_SERVER_CONTEXT_SIZE,
        threads: int = LLM_SERVER_THREADS,
        gpu_layers: int = LLM_SERVER_GPU_LAYERS,
        batch_size: int = LLM_SERVER_BATCH_SIZE,
    ):
        """
        Initialize LLM Server

        Args:
            host: Server host address
            port: Server port number
            context_size: Context window size
            threads: Number of CPU threads
            gpu_layers: Number of GPU layers
            batch_size: Batch size for processing
        """
        self.host = host
        self.port = port
        self.context_size = context_size
        self.threads = threads
        self.gpu_layers = gpu_layers
        self.batch_size = batch_size

        self.process: Optional[subprocess.Popen] = None
        self.current_model: Optional[str] = None
        self.current_model_path: Optional[Path] = None
        self.status: str = MODEL_STATUS_NOT_STARTED
        self.error_message: Optional[str] = None

    def start_server(self, model_path: str, model_name: str) -> bool:
        """
        Start the LLM server with specified model

        Args:
            model_path: Path to the GGUF model file
            model_name: Name of the model

        Returns:
            True if server started successfully, False otherwise
        """
        # Check if model file exists
        model_file = Path(model_path)
        if not model_file.exists():
            self.status = MODEL_STATUS_ERROR
            self.error_message = f"Model file not found: {model_path}"
            logger.error(self.error_message)
            return False

        # Check if it's a GGUF file
        if not model_file.suffix.lower() == '.gguf':
            self.status = MODEL_STATUS_ERROR
            self.error_message = f"Invalid model file format. Expected .gguf file: {model_path}"
            logger.error(self.error_message)
            return False

        # Stop existing server if running
        if self.process is not None:
            self.stop_server()

        self.status = MODEL_STATUS_STARTING
        self.current_model = model_name
        self.current_model_path = model_file

        try:
            # Build llama-server command
            cmd = [
                "llama-server",
                "-m", str(model_file),
                "-t", str(self.threads),
                "--host", self.host,
                "--port", str(self.port),
                "--ctx-size", str(self.context_size),
                "--n-gpu-layers", str(self.gpu_layers),
                "--batch-size", str(self.batch_size),
                "--metrics",
                "--no-mmap"
            ]

            logger.info(f"Starting LLM server with command: {' '.join(cmd)}")

            # Start the server process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )

            # Wait for server to start (check health endpoint)
            max_retries = 30
            retry_interval = 2
            for i in range(max_retries):
                try:
                    time.sleep(retry_interval)
                    response = requests.get(f"http://{self.host}:{self.port}/health", timeout=5)
                    if response.status_code == 200:
                        self.status = MODEL_STATUS_RUNNING
                        self.error_message = None
                        logger.info(f"LLM server started successfully with model: {model_name}")
                        return True
                except requests.exceptions.RequestException:
                    logger.info(f"Waiting for server to start... ({i+1}/{max_retries})")
                    continue

            # If we get here, server didn't start
            self.status = MODEL_STATUS_ERROR
            self.error_message = "Server failed to start within timeout period"
            self.stop_server()
            return False

        except FileNotFoundError:
            self.status = MODEL_STATUS_ERROR
            self.error_message = "llama-server executable not found. Please install llama.cpp"
            logger.error(self.error_message)
            return False
        except Exception as e:
            self.status = MODEL_STATUS_ERROR
            self.error_message = f"Failed to start server: {str(e)}"
            logger.error(self.error_message)
            return False

    def stop_server(self) -> bool:
        """
        Stop the running LLM server

        Returns:
            True if server stopped successfully
        """
        if self.process is None:
            logger.info("No server process to stop")
            return True

        try:
            # Send SIGTERM to the entire process group
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

            # Wait for process to terminate
            self.process.wait(timeout=10)
            logger.info("LLM server stopped successfully")

        except subprocess.TimeoutExpired:
            # Force kill if it doesn't stop gracefully
            os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
            logger.warning("LLM server force killed")

        except Exception as e:
            logger.error(f"Error stopping server: {str(e)}")
            return False

        finally:
            self.process = None
            self.status = MODEL_STATUS_STOPPED
            self.current_model = None
            self.current_model_path = None

        return True

    def switch_model(self, model_path: str, model_name: str) -> bool:
        """
        Switch to a different model

        Args:
            model_path: Path to the new model file
            model_name: Name of the new model

        Returns:
            True if model switched successfully
        """
        logger.info(f"Switching model to: {model_name}")
        return self.start_server(model_path, model_name)

    def get_status(self) -> Dict[str, Any]:
        """
        Get current server status

        Returns:
            Dictionary containing server status information
        """
        return {
            "status": self.status,
            "model_name": self.current_model,
            "model_path": str(self.current_model_path) if self.current_model_path else None,
            "error_message": self.error_message,
            "is_running": self.process is not None and self.process.poll() is None
        }


class LLMClient:
    """LLM Client for interacting with the LLM server"""

    def __init__(
        self,
        base_url: str = LLM_CLIENT_BASE_URL,
        temperature: float = LLM_CLIENT_TEMPERATURE,
        repeat_penalty: float = LLM_CLIENT_REPEAT_PENALTY,
        max_tokens: int = LLM_CLIENT_MAX_TOKENS
    ):
        """
        Initialize LLM Client

        Args:
            base_url: Base URL of the LLM server
            temperature: Sampling temperature
            repeat_penalty: Repetition penalty
            max_tokens: Maximum tokens to generate
        """
        self.base_url = base_url
        self.temperature = temperature
        self.repeat_penalty = repeat_penalty
        self.max_tokens = max_tokens

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: Optional[float] = None,
        repeat_penalty: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Any:
        """
        Send chat completion request

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            stream: Whether to stream the response
            temperature: Override default temperature
            repeat_penalty: Override default repeat penalty
            max_tokens: Override default max tokens

        Returns:
            Response from the server (dict if not streaming, iterator if streaming)
        """
        url = f"{self.base_url}/chat/completions"

        payload = {
            "messages": messages,
            "temperature": temperature or self.temperature,
            "repeat_penalty": repeat_penalty or self.repeat_penalty,
            "max_tokens": max_tokens or self.max_tokens,
            "stream": stream
        }

        if stream:
            return self._stream_chat_completion(url, payload)
        else:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()

    def _stream_chat_completion(self, url: str, payload: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """
        Stream chat completion response

        Args:
            url: API endpoint URL
            payload: Request payload

        Yields:
            Chunks of the streaming response
        """
        import json

        with requests.post(url, json=payload, stream=True, timeout=300) as response:
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            yield data
                        except json.JSONDecodeError:
                            continue

    def update_parameters(
        self,
        temperature: Optional[float] = None,
        repeat_penalty: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """
        Update client parameters

        Args:
            temperature: New temperature value
            repeat_penalty: New repeat penalty value
            max_tokens: New max tokens value
        """
        if temperature is not None:
            self.temperature = temperature
        if repeat_penalty is not None:
            self.repeat_penalty = repeat_penalty
        if max_tokens is not None:
            self.max_tokens = max_tokens
