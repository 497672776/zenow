"""
Model Server Manager for managing multiple concurrent llama-server processes
"""
import logging
from typing import Dict, Optional
from .llm import LLMServer, LLMClient
from .embed import EmbedServer, EmbedClient
from .rerank import RerankServer, RerankClient

logger = logging.getLogger(__name__)


class ModelServerManager:
    """
    管理多个模型服务器实例（LLM, Embed, Rerank）
    每个模式可以同时运行一个 llama-server 进程
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        llm_port: int = 8051,
        embed_port: int = 8052,
        rerank_port: int = 8053,
        context_size: int = 15360,
        threads: int = 8,
        gpu_layers: int = 0,
        batch_size: int = 512
    ):
        """
        初始化模型服务器管理器

        Args:
            host: 服务器主机地址
            llm_port: LLM 模型服务器端口
            embed_port: Embed 模型服务器端口
            rerank_port: Rerank 模型服务器端口
            context_size: 默认上下文窗口大小
            threads: 默认 CPU 线程数
            gpu_layers: 默认 GPU 层数
            batch_size: 默认批处理大小
        """
        self.host = host
        self.servers: Dict[str, any] = {}
        self.clients: Dict[str, any] = {}

        # 创建 LLM 服务器实例
        self.servers["llm"] = LLMServer(
            host=host,
            port=llm_port,
            context_size=context_size,
            threads=threads,
            gpu_layers=gpu_layers,
            batch_size=batch_size
        )

        # 创建 Embed 服务器实例
        self.servers["embed"] = EmbedServer(
            host=host,
            port=embed_port,
            context_size=8192,  # Embed 通常需要较小的上下文
            threads=threads,
            gpu_layers=gpu_layers,
            batch_size=batch_size,
            embedding=True
        )

        # 创建 Rerank 服务器实例
        self.servers["rerank"] = RerankServer(
            host=host,
            port=rerank_port,
            context_size=8192,  # Rerank 通常需要较小的上下文
            threads=threads,
            gpu_layers=gpu_layers,
            batch_size=batch_size,
            reranking=True
        )

        # 创建对应的客户端实例
        self.clients["llm"] = LLMClient(
            base_url=f"http://{host}:{llm_port}/v1",
            temperature=0.7,
            repeat_penalty=1.1,
            max_tokens=2048
        )

        self.clients["embed"] = EmbedClient(
            base_url=f"http://{host}:{embed_port}/v1",
            normalize=True,
            truncate=True
        )

        self.clients["rerank"] = RerankClient(
            base_url=f"http://{host}:{rerank_port}/v1",
            top_n=10,
            return_documents=True
        )

        logger.info(f"ModelServerManager initialized with ports: LLM={llm_port}, Embed={embed_port}, Rerank={rerank_port}")

    def get_server(self, mode: str = "llm"):
        """
        获取指定模式的服务器实例

        Args:
            mode: 模型模式 ('llm', 'embed', 'rerank')

        Returns:
            对应模式的服务器实例

        Raises:
            ValueError: 如果模式无效
        """
        if mode not in self.servers:
            raise ValueError(f"Invalid mode: {mode}. Must be 'llm', 'embed', or 'rerank'")
        return self.servers[mode]

    def get_client(self, mode: str = "llm"):
        """
        获取指定模式的客户端实例

        Args:
            mode: 模型模式 ('llm', 'embed', 'rerank')

        Returns:
            对应模式的客户端实例

        Raises:
            ValueError: 如果模式无效
        """
        if mode not in self.clients:
            raise ValueError(f"Invalid mode: {mode}. Must be 'llm', 'embed', or 'rerank'")
        return self.clients[mode]

    def get_all_statuses(self) -> Dict[str, Dict]:
        """
        获取所有服务器的状态

        Returns:
            包含所有模式状态的字典
        """
        return {
            mode: server.get_status()
            for mode, server in self.servers.items()
        }

    async def stop_all(self):
        """停止所有运行中的服务器"""
        logger.info("Stopping all model servers...")
        for mode, server in self.servers.items():
            try:
                await server.stop()
                logger.info(f"Stopped {mode} server")
            except Exception as e:
                logger.error(f"Error stopping {mode} server: {e}")

    def get_port(self, mode: str = "llm") -> int:
        """
        获取指定模式的端口号

        Args:
            mode: 模型模式 ('llm', 'embed', 'rerank')

        Returns:
            端口号
        """
        server = self.get_server(mode)
        return server.port

