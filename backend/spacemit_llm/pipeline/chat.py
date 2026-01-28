"""
Chat Pipeline
"""

import json
import logging
from typing import AsyncIterator, Optional

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from ..model.server_manager import ModelServerManager
from ..comon.sqlite.sqlite_config import SQLiteConfig
from ..comon.sqlite.sqlite_session import SQLiteSession
from ..utils.token_estimator import estimate_message_tokens

logger = logging.getLogger(__name__)


class ChatPipeline:
    """Chat pipeline manager"""

    def __init__(
        self,
        server_manager: ModelServerManager,
        db_config: SQLiteConfig,
        db_session: SQLiteSession,
        default_system_prompt: str = "You are a helpful assistant.",
        default_context_size: int = 15360
    ):
        self.server_manager = server_manager
        self.db_config = db_config
        self.db_session = db_session
        self.default_system_prompt = default_system_prompt
        self.default_context_size = default_context_size

    async def process_chat(self, request) -> StreamingResponse:
        """
        Process chat request and return streaming response

        Args:
            request: Chat request containing message, session_id, and optional parameters

        Returns:
            StreamingResponse with SSE format
        """
        try:
            # 验证 session_id 必须提供
            if request.session_id is None:
                raise HTTPException(
                    status_code=400,
                    detail="session_id is required. Please create a session first."
                )

            mode = request.mode or "llm"

            # 获取对应模式的服务器和客户端
            server = self.server_manager.get_server(mode)
            client = self.server_manager.get_client(mode)

            # 检查服务器是否运行
            status = server.get_status()
            if not status["is_running"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"{mode.upper()} server is not running. Please select a model first."
                )

            # 验证会话是否存在
            session = self.db_session.get_session(request.session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            # 获取系统提示词
            system_prompt_param = self.db_config.get_parameter("system_prompt")
            system_prompt = system_prompt_param if system_prompt_param else self.default_system_prompt

            # 估算系统提示词的 token 数
            system_prompt_tokens = estimate_message_tokens("system", system_prompt)

            # 获取 context_size 参数
            context_size_param = self.db_config.get_parameter("context_size")
            context_size = context_size_param if context_size_param else self.default_context_size

            # 计算历史记录的最大 token 数（context_size 的一半）
            max_history_tokens = context_size // 2

            # 从数据库加载历史消息（在 token 限制内）
            history_messages = self.db_session.get_messages_within_token_limit(
                session_id=request.session_id,
                max_tokens=max_history_tokens,
                system_prompt_tokens=system_prompt_tokens
            )

            # 构建消息列表：[system] + [history] + [new_user_message]
            messages_to_send = []
            messages_to_send.append({"role": "system", "content": system_prompt})

            # 添加历史消息
            for msg in history_messages:
                messages_to_send.append({"role": msg["role"], "content": msg["content"]})

            # 添加新的用户消息
            if request.message:
                new_user_message = request.message
                messages_to_send.append({"role": new_user_message.role, "content": new_user_message.content})

                # 保存用户消息到数据库
                user_token_count = estimate_message_tokens(new_user_message.role, new_user_message.content)
                self.db_session.add_message(
                    session_id=request.session_id,
                    role=new_user_message.role,
                    content=new_user_message.content,
                    token_count=user_token_count
                )

            # 流式响应生成器
            async def generate():
                assistant_response = ""  # 收集完整的助手响应
                try:
                    stream_gen = client.chat_stream(
                        messages=messages_to_send,
                        temperature=request.temperature,
                        repeat_penalty=request.repeat_penalty,
                        max_tokens=request.max_tokens
                    )
                    async for chunk in stream_gen:
                        # 收集文本内容
                        content = chunk.get("data", "")
                        done_flag = chunk.get("done_flag", False)

                        if content:
                            assistant_response += content

                        # 直接发送结构化数据给前端
                        yield f"data: {json.dumps(chunk)}\n\n"

                        if done_flag:
                            break

                    # 保存助手响应到数据库
                    if assistant_response:
                        assistant_token_count = estimate_message_tokens("assistant", assistant_response)
                        self.db_session.add_message(
                            session_id=request.session_id,
                            role="assistant",
                            content=assistant_response,
                            token_count=assistant_token_count
                        )
                        logger.info(f"Saved assistant message to session {request.session_id}, tokens: {assistant_token_count}")

                except Exception as e:
                    logger.error(f"Error in chat stream: {e}", exc_info=True)
                    error_data = {"error": str(e)}
                    yield f"data: {json.dumps(error_data)}\n\n"

            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )

        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))