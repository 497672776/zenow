"""
模型参数修改 Pipeline
处理 LLM 参数的更新、持久化和服务重启
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ModelParameterChangePipeline:
    """处理模型参数修改的完整流程"""

    def __init__(self, llm_server, llm_client, db_config):
        """
        初始化参数修改 Pipeline

        Args:
            llm_server: LLMServer 实例
            llm_client: LLMClient 实例
            db_config: SQLiteConfig 实例
        """
        self.llm_server = llm_server
        self.llm_client = llm_client
        self.db_config = db_config

    async def apply_parameters(
        self,
        # LLMServer 参数
        context_size: Optional[int] = None,
        threads: Optional[int] = None,
        gpu_layers: Optional[int] = None,
        batch_size: Optional[int] = None,
        # LLMClient 参数
        temperature: Optional[float] = None,
        repeat_penalty: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        应用参数修改

        流程：
        1. 验证参数合法性
        2. 更新 LLMServer 参数（如有）并重启服务
        3. 更新 LLMClient 参数（如有）
        4. 持久化到数据库
        5. 返回结果

        Returns:
            包含成功状态、消息和是否重启的字典
        """
        logger.info("=" * 80)
        logger.info("参数修改 Pipeline - 开始应用新参数")
        logger.info("=" * 80)

        try:
            requires_restart = False
            updated_params = []

            # Step 1: 验证参数
            self._validate_parameters(
                context_size, threads, gpu_layers, batch_size,
                temperature, repeat_penalty, max_tokens
            )

            # Step 2: 更新 LLMServer 参数（需要重启）
            server_params_changed = await self._update_server_parameters(
                context_size, threads, gpu_layers, batch_size
            )

            if server_params_changed:
                requires_restart = True
                if context_size is not None:
                    updated_params.append(f"context_size={context_size}")
                if threads is not None:
                    updated_params.append(f"threads={threads}")
                if gpu_layers is not None:
                    updated_params.append(f"gpu_layers={gpu_layers}")
                if batch_size is not None:
                    updated_params.append(f"batch_size={batch_size}")

            # Step 3: 更新 LLMClient 参数（立即生效）
            client_params_changed = self._update_client_parameters(
                temperature, repeat_penalty, max_tokens
            )

            if client_params_changed:
                if temperature is not None:
                    updated_params.append(f"temperature={temperature}")
                if repeat_penalty is not None:
                    updated_params.append(f"repeat_penalty={repeat_penalty}")
                if max_tokens is not None:
                    updated_params.append(f"max_tokens={max_tokens}")

            # Step 4: 持久化到数据库
            await self._persist_parameters(
                context_size, threads, gpu_layers, batch_size,
                temperature, repeat_penalty, max_tokens
            )

            # 构建返回消息
            if not updated_params:
                message = "未检测到参数变化"
            else:
                message = f"参数更新成功: {', '.join(updated_params)}"
                if requires_restart:
                    message += " (已重启 llama-server 以应用新配置)"

            logger.info(f"✓ {message}")
            logger.info("=" * 80)

            return {
                "success": True,
                "message": message,
                "requires_restart": requires_restart
            }

        except Exception as e:
            logger.error(f"✗ 参数更新失败: {e}", exc_info=True)
            logger.info("=" * 80)
            return {
                "success": False,
                "message": f"参数更新失败: {str(e)}",
                "requires_restart": False
            }

    def _validate_parameters(
        self,
        context_size: Optional[int],
        threads: Optional[int],
        gpu_layers: Optional[int],
        batch_size: Optional[int],
        temperature: Optional[float],
        repeat_penalty: Optional[float],
        max_tokens: Optional[int]
    ) -> None:
        """验证参数合法性"""
        if context_size is not None and context_size <= 0:
            raise ValueError(f"context_size must be > 0, got: {context_size}")
        if threads is not None and threads <= 0:
            raise ValueError(f"threads must be > 0, got: {threads}")
        if gpu_layers is not None and gpu_layers < 0:
            raise ValueError(f"gpu_layers cannot be negative, got: {gpu_layers}")
        if batch_size is not None and batch_size <= 0:
            raise ValueError(f"batch_size must be > 0, got: {batch_size}")
        if temperature is not None and (temperature < 0 or temperature > 2):
            raise ValueError(f"temperature must be 0-2, got: {temperature}")
        if repeat_penalty is not None and repeat_penalty < 0:
            raise ValueError(f"repeat_penalty cannot be negative, got: {repeat_penalty}")
        if max_tokens is not None and max_tokens <= 0:
            raise ValueError(f"max_tokens must be > 0, got: {max_tokens}")
        logger.info("✓ 参数验证通过")

    async def _update_server_parameters(
        self,
        context_size: Optional[int],
        threads: Optional[int],
        gpu_layers: Optional[int],
        batch_size: Optional[int]
    ) -> bool:
        """
        更新 LLMServer 参数（检测是否真正变化）

        Returns:
            是否有参数变化且需要重启
        """
        # 检查是否有任何参数被提供
        params_provided = any([
            context_size is not None,
            threads is not None,
            gpu_layers is not None,
            batch_size is not None
        ])

        if not params_provided:
            logger.info("ℹ 未提供 LLMServer 参数变化")
            return False

        # 检查参数是否真正变化
        actual_changes = []
        if context_size is not None and context_size != self.llm_server.context_size:
            actual_changes.append(f"context_size: {self.llm_server.context_size} → {context_size}")
        if threads is not None and threads != self.llm_server.threads:
            actual_changes.append(f"threads: {self.llm_server.threads} → {threads}")
        if gpu_layers is not None and gpu_layers != self.llm_server.gpu_layers:
            actual_changes.append(f"gpu_layers: {self.llm_server.gpu_layers} → {gpu_layers}")
        if batch_size is not None and batch_size != self.llm_server.batch_size:
            actual_changes.append(f"batch_size: {self.llm_server.batch_size} → {batch_size}")

        # 如果没有实际变化，跳过更新
        if not actual_changes:
            logger.info("ℹ LLMServer 参数无实际变化，跳过重启")
            return False

        # 有实际变化，执行更新和重启
        logger.info("→ 检测到 LLMServer 参数变化:")
        for change in actual_changes:
            logger.info(f"  - {change}")

        success = await self.llm_server.update_params(
            context_size=context_size,
            threads=threads,
            gpu_layers=gpu_layers,
            batch_size=batch_size
        )

        if success:
            logger.info("✓ LLMServer 参数更新成功（已重启服务）")
        else:
            raise Exception("LLMServer 参数更新失败")

        return True

    def _update_client_parameters(
        self,
        temperature: Optional[float],
        repeat_penalty: Optional[float],
        max_tokens: Optional[int]
    ) -> bool:
        """
        更新 LLMClient 参数（检测是否真正变化）

        Returns:
            是否有参数变化
        """
        # 检查是否有任何参数被提供
        params_provided = any([
            temperature is not None,
            repeat_penalty is not None,
            max_tokens is not None
        ])

        if not params_provided:
            logger.info("ℹ 未提供 LLMClient 参数变化")
            return False

        # 检查参数是否真正变化
        actual_changes = []
        if temperature is not None and temperature != self.llm_client.temperature:
            actual_changes.append(f"temperature: {self.llm_client.temperature} → {temperature}")
        if repeat_penalty is not None and repeat_penalty != self.llm_client.repeat_penalty:
            actual_changes.append(f"repeat_penalty: {self.llm_client.repeat_penalty} → {repeat_penalty}")
        if max_tokens is not None and max_tokens != self.llm_client.max_tokens:
            actual_changes.append(f"max_tokens: {self.llm_client.max_tokens} → {max_tokens}")

        # 如果没有实际变化，跳过更新
        if not actual_changes:
            logger.info("ℹ LLMClient 参数无实际变化，跳过更新")
            return False

        # 有实际变化，执行更新
        logger.info("→ 检测到 LLMClient 参数变化:")
        for change in actual_changes:
            logger.info(f"  - {change}")

        self.llm_client.update_parameters(
            temperature=temperature,
            repeat_penalty=repeat_penalty,
            max_tokens=max_tokens
        )

        logger.info("✓ LLMClient 参数更新成功")
        return True

    async def _persist_parameters(
        self,
        context_size: Optional[int],
        threads: Optional[int],
        gpu_layers: Optional[int],
        batch_size: Optional[int],
        temperature: Optional[float],
        repeat_penalty: Optional[float],
        max_tokens: Optional[int]
    ) -> None:
        """将参数持久化到数据库"""
        logger.info("→ 持久化参数到数据库...")
        import asyncio
        def _save():
            if context_size is not None:
                self.db_config.set_parameter("context_size", context_size, "int")
            if threads is not None:
                self.db_config.set_parameter("threads", threads, "int")
            if gpu_layers is not None:
                self.db_config.set_parameter("gpu_layers", gpu_layers, "int")
            if batch_size is not None:
                self.db_config.set_parameter("batch_size", batch_size, "int")
            if temperature is not None:
                self.db_config.set_parameter("temperature", temperature, "float")
            if repeat_penalty is not None:
                self.db_config.set_parameter("repeat_penalty", repeat_penalty, "float")
            if max_tokens is not None:
                self.db_config.set_parameter("max_tokens", max_tokens, "int")
        await asyncio.to_thread(_save)
        logger.info("✓ 参数已保存到数据库")
