"""
Embed Server and Client implementation for Zenow backend
"""
import subprocess
import os
import signal
import time
import requests  # For sync health checks
import httpx  # For async client
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model status constants
MODEL_STATUS_NOT_STARTED = "not_started"
MODEL_STATUS_STARTING = "starting"
MODEL_STATUS_RUNNING = "running"
MODEL_STATUS_ERROR = "error"
MODEL_STATUS_STOPPED = "stopped"


class EmbedServer:
    """Embed Server 管理类 - 用于文本嵌入模型"""

    def __init__(
        self,
        host: str,
        port: int,
        context_size: int = 8192,  # Embed 模型通常需要较小的上下文
        threads: int = 8,
        gpu_layers: int = 0,
        batch_size: int = 512,
        embedding: bool = True  # Embed 模式特有参数
    ):
        """
        初始化 Embed Server

        Args:
            host: 服务器主机地址
            port: 服务器端口号
            context_size: 上下文窗口大小
            threads: CPU 线程数
            gpu_layers: GPU 层数
            batch_size: 批处理大小
            embedding: 启用嵌入模式
        """
        self.host = host
        self.port = port
        self.context_size = context_size
        self.threads = threads
        self.gpu_layers = gpu_layers
        self.batch_size = batch_size
        self.embedding = embedding

        self.process: Optional[subprocess.Popen] = None
        self.current_model: Optional[str] = None
        self.current_model_path: Optional[Path] = None
        self.status: str = MODEL_STATUS_NOT_STARTED
        self.error_message: Optional[str] = None

    def start_server(self, model_path: str, model_name: str) -> bool:
        """
        Start the Embed server with specified model

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
            # Build llama-server command for embedding mode
            cmd = [
                "llama-server",
                "-m", str(model_file),
                "-t", str(self.threads),
                "--host", self.host,
                "--port", str(self.port),
                "--ctx-size", str(self.context_size),
                "--n-gpu-layers", str(self.gpu_layers),
                "--batch-size", str(self.batch_size),
                "--embedding",  # 启用嵌入模式
                "--metrics",
                "--no-mmap"
            ]

            logger.info(f"Starting Embed server with command: {' '.join(cmd)}")

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
                        logger.info(f"Embed server started successfully with model: {model_name}")
                        return True
                except requests.exceptions.RequestException:
                    logger.info(f"Waiting for Embed server to start... ({i+1}/{max_retries})")
                    continue

            # If we get here, server didn't start
            self.status = MODEL_STATUS_ERROR
            self.error_message = "Embed server failed to start within timeout period"
            self.stop_server()
            return False

        except FileNotFoundError:
            self.status = MODEL_STATUS_ERROR
            self.error_message = "llama-server executable not found. Please install llama.cpp"
            logger.error(self.error_message)
            return False
        except Exception as e:
            self.status = MODEL_STATUS_ERROR
            self.error_message = f"Failed to start Embed server: {str(e)}"
            logger.error(self.error_message)
            return False

    def stop_server(self) -> bool:
        """
        Stop the running Embed server

        Returns:
            True if server stopped successfully
        """
        if self.process is None:
            logger.info("No Embed server process to stop")
            return True

        try:
            # Send SIGTERM to the entire process group
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

            # Wait for process to terminate
            self.process.wait(timeout=10)
            logger.info("Embed server stopped successfully")

        except subprocess.TimeoutExpired:
            # Force kill if it doesn't stop gracefully
            os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
            logger.warning("Embed server force killed")

        except Exception as e:
            logger.error(f"Error stopping Embed server: {str(e)}")
            return False

        finally:
            self.process = None
            self.status = MODEL_STATUS_STOPPED
            self.current_model = None
            self.current_model_path = None

        return True

    def switch_model(self, model_path: str, model_name: str) -> bool:
        """
        Switch to a different embedding model

        Args:
            model_path: Path to the new model file
            model_name: Name of the new model

        Returns:
            True if model switched successfully
        """
        logger.info(f"Switching Embed model to: {model_name}")
        return self.start_server(model_path, model_name)

    def get_status(self) -> Dict[str, Any]:
        """
        Get current Embed server status

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

    def update_parameters(
        self,
        context_size: Optional[int] = None,
        threads: Optional[int] = None,
        gpu_layers: Optional[int] = None,
        batch_size: Optional[int] = None
    ) -> bool:
        """
        更新 Embed Server 参数（需要重启进程才能生效）

        Args:
            context_size: 上下文窗口大小
            threads: CPU 线程数
            gpu_layers: GPU 层数
            batch_size: 批处理大小

        Returns:
            True if parameters updated successfully
        """
        # 更新参数
        if context_size is not None:
            self.context_size = context_size
        if threads is not None:
            self.threads = threads
        if gpu_layers is not None:
            self.gpu_layers = gpu_layers
        if batch_size is not None:
            self.batch_size = batch_size

        # 如果服务器正在运行，需要重启以应用新参数
        if self.process is not None and self.current_model_path:
            logger.info("EmbedServer 参数已更新，重启进程以应用新配置...")
            model_path = str(self.current_model_path)
            model_name = self.current_model
            return self.start_server(model_path, model_name)

        logger.info("EmbedServer 参数已更新（服务器未运行，启动时将应用新配置）")
        return True

    async def update_params(
        self,
        context_size: Optional[int] = None,
        threads: Optional[int] = None,
        gpu_layers: Optional[int] = None,
        batch_size: Optional[int] = None
    ) -> bool:
        """
        异步更新 Embed Server 参数

        Args:
            context_size: 上下文窗口大小
            threads: CPU 线程数
            gpu_layers: GPU 层数
            batch_size: 批处理大小

        Returns:
            True if parameters updated successfully
        """
        import asyncio
        return await asyncio.to_thread(
            self.update_parameters,
            context_size,
            threads,
            gpu_layers,
            batch_size
        )

    async def start(self, model_path: str, model_name: str) -> bool:
        """Async wrapper for start_server"""
        import asyncio
        return await asyncio.to_thread(self.start_server, model_path, model_name)

    async def stop(self) -> bool:
        """Async wrapper for stop_server"""
        import asyncio
        return await asyncio.to_thread(self.stop_server)

    async def switch(self, model_path: str, model_name: str) -> bool:
        """Async wrapper for switch_model"""
        import asyncio
        return await asyncio.to_thread(self.switch_model, model_path, model_name)


class EmbedClient:
    """Embed Client 用于与 Embed server 交互"""

    def __init__(
        self,
        base_url: str,
        normalize: bool = True,  # 是否归一化嵌入向量
        truncate: bool = True    # 是否截断过长文本
    ):
        """
        初始化 Embed Client

        Args:
            base_url: Embed server 的基础 URL
            normalize: 是否归一化嵌入向量
            truncate: 是否截断过长文本
        """
        self.base_url = base_url
        self.normalize = normalize
        self.truncate = truncate

    async def get_embeddings(
        self,
        texts: List[str],
        normalize: Optional[bool] = None,
        truncate: Optional[bool] = None
    ) -> List[List[float]]:
        """
        获取文本的嵌入向量

        Args:
            texts: 文本列表
            normalize: 是否归一化（覆盖默认值）
            truncate: 是否截断（覆盖默认值）

        Returns:
            嵌入向量列表
        """
        norm = normalize if normalize is not None else self.normalize
        trunc = truncate if truncate is not None else self.truncate

        payload = {
            "input": texts,
            "normalize": norm,
            "truncate": trunc
        }

        url = f"{self.base_url}/embeddings"

        async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            # 提取嵌入向量
            embeddings = [item["embedding"] for item in data.get("data", [])]
            return embeddings

    async def get_embedding(
        self,
        text: str,
        normalize: Optional[bool] = None,
        truncate: Optional[bool] = None
    ) -> List[float]:
        """
        获取单个文本的嵌入向量

        Args:
            text: 文本
            normalize: 是否归一化
            truncate: 是否截断

        Returns:
            嵌入向量
        """
        embeddings = await self.get_embeddings([text], normalize, truncate)
        return embeddings[0] if embeddings else []

    def update_parameters(
        self,
        normalize: Optional[bool] = None,
        truncate: Optional[bool] = None
    ):
        """
        更新客户端参数

        Args:
            normalize: 是否归一化
            truncate: 是否截断
        """
        if normalize is not None:
            self.normalize = normalize
        if truncate is not None:
            self.truncate = truncate
