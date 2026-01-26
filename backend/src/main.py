# -*- coding: utf-8 -*-
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

from src.model.llm import LLMServer, LLMClient
from src.model.server_manager import ModelServerManager
from src.model.download import ModelDownloader
from src.comon.sqlite.sqlite_config import SQLiteConfig
from src.comon.sqlite.sqlite_session import SQLiteSession
from src.pipeline.model_select import ModelSelectionPipeline
from src.pipeline.backend_exit import BackendExitHandler
from src.pipeline.backend_start import BackendStartupHandler
from src.pipeline.model_param_change import ModelParameterChangePipeline
from src.utils.token_estimator import estimate_message_tokens
from src import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def write_port_file(port: int):
    """Write the port number to a file for frontend to read."""
    port_file = Path.home() / ".config" / "zenow" / "backend.port"
    port_file.parent.mkdir(parents=True, exist_ok=True)

    # Write port with PID to detect stale files
    port_file.write_text(f"{port}\n{os.getpid()}\n")
    logger.info(f"📝 Wrote port {port} and PID {os.getpid()} to {port_file}")


def cleanup_port_file():
    """Remove port file on shutdown."""
    port_file = Path.home() / ".config" / "zenow" / "backend.port"
    if port_file.exists():
        port_file.unlink()
        logger.info(f"🧹 Cleaned up port file: {port_file}")


app = FastAPI(title="Zenow LLM Chat API")

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    write_port_file(config.API_SERVER_PORT)

    # Initialize database and start model
    await startup_handler.initialize()


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up port file on shutdown."""
    cleanup_port_file()


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
db_config = SQLiteConfig(config.DB_CONFIG_PATH)
db_session = SQLiteSession(config.DB_SESSION_PATH)

# 使用 ModelServerManager 管理多个服务器实例
server_manager = ModelServerManager(
    host=config.LLM_SERVER_HOST,
    llm_port=config.LLM_SERVER_PORT,
    embed_port=config.EMBED_SERVER_PORT,
    rerank_port=config.RERANK_SERVER_PORT,
    context_size=config.LLM_SERVER_CONTEXT_SIZE,
    threads=config.LLM_SERVER_THREADS,
    gpu_layers=config.LLM_SERVER_GPU_LAYERS,
    batch_size=config.LLM_SERVER_BATCH_SIZE
)

# 获取 LLM 模式的服务器和客户端（用于向后兼容）
llm_server = server_manager.get_server("llm")
llm_client = server_manager.get_client("llm")

model_downloader = ModelDownloader(config.LLM_MODELS_DIR)
model_selection_pipeline = ModelSelectionPipeline(
    models_dir=config.LLM_MODELS_DIR,
    downloader=model_downloader,
    server_manager=server_manager,
    db_config=db_config
)

# Register exit handler to clean up all llama-servers on backend exit
exit_handler = BackendExitHandler(server_manager)
exit_handler.register()

# Register startup handler to initialize database and start all current models
startup_handler = BackendStartupHandler(server_manager, db_config, config)

# Register parameter change pipeline
param_change_pipeline = ModelParameterChangePipeline(llm_server, llm_client, db_config)

# Models
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    stream: Optional[bool] = False
    temperature: Optional[float] = None
    repeat_penalty: Optional[float] = None
    max_tokens: Optional[int] = None
    mode: Optional[str] = "llm"  # Added mode parameter
    session_id: Optional[int] = None  # Optional session ID for history management

class ChatResponse(BaseModel):
    message: Message
    model: str

class ModelInfo(BaseModel):
    id: int
    name: str
    path: str
    is_downloaded: bool
    mode: Optional[str] = "llm"  # Added mode field

class ModelListResponse(BaseModel):
    models: List[ModelInfo]
    current_model: Optional[ModelInfo] = None

class AddModelRequest(BaseModel):
    name: str
    path: str
    mode: Optional[str] = "llm"  # Added mode parameter

class ServerStatusResponse(BaseModel):
    status: str
    model_name: Optional[str] = None
    model_path: Optional[str] = None
    is_running: bool
    error_message: Optional[str] = None

class DownloadModelRequest(BaseModel):
    url: str
    filename: Optional[str] = None
    mode: Optional[str] = "llm"  # Added mode parameter

class DownloadStatusResponse(BaseModel):
    url: str
    filename: str
    status: str  # downloading, completed, failed
    downloaded: int
    total: int
    progress: float
    error: Optional[str] = None

class DefaultDownloadUrlsResponse(BaseModel):
    urls: Dict[str, List[str]]  # Changed to dict by mode
    browser_path: str

class SelectModelRequest(BaseModel):
    model_name: str
    download_url: Optional[str] = None
    mode: Optional[str] = "llm"  # Added mode parameter

class SelectModelResponse(BaseModel):
    success: bool
    message: str
    model_name: str
    model_path: Optional[str]
    server_status: str

class LLMParametersRequest(BaseModel):
    # LLMServer 参数
    context_size: Optional[int] = None
    threads: Optional[int] = None
    gpu_layers: Optional[int] = None
    batch_size: Optional[int] = None
    # LLMClient 参数
    temperature: Optional[float] = None
    repeat_penalty: Optional[float] = None
    max_tokens: Optional[int] = None

class LLMParametersResponse(BaseModel):
    # LLMServer 参数
    context_size: int
    threads: int
    gpu_layers: int
    batch_size: int
    # LLMClient 参数
    temperature: float
    repeat_penalty: float
    max_tokens: int

class UpdateParametersResponse(BaseModel):
    success: bool
    message: str
    requires_restart: bool

# ==================== Session Management Models ====================

class SessionInfo(BaseModel):
    id: int
    session_name: str
    created_at: str
    updated_at: str
    message_count: int
    total_tokens: int

class SessionListResponse(BaseModel):
    sessions: List[SessionInfo]
    total: int

class CreateSessionRequest(BaseModel):
    first_message: str

class CreateSessionResponse(BaseModel):
    session_id: int
    session_name: str

class UpdateSessionNameRequest(BaseModel):
    new_name: str

class MessageInfo(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    token_count: int
    created_at: str

class MessagesResponse(BaseModel):
    messages: List[MessageInfo]
    session_id: int
    total_tokens: int

class AddMessageRequest(BaseModel):
    role: str
    content: str

class AddMessageResponse(BaseModel):
    message_id: int
    token_count: int



@app.get("/")
async def root():
    return {"message": "Zenow LLM Chat API"}


# ============================================================================
# 核心 API 端点 (6个)
# ============================================================================

@app.get("/api/models/current")
async def get_current_model(mode: str = "llm"):
    """
    获取当前模型

    Args:
        mode: 模型模式 ('llm', 'embed', 'rerank')

    Returns:
        当前模型信息，如果没有则返回 None
    """
    try:
        current = db_config.get_current_model(mode=mode)
        if current:
            # 检查并更新下载状态
            db_config.check_and_update_download_status(current["id"])
            # 重新获取更新后的状态
            current = db_config.get_current_model(mode=mode)

            return {
                "id": current["id"],
                "name": current["model_name"],
                "path": current["model_path"],
                "is_downloaded": bool(current.get("is_downloaded", False)),
                "mode": current.get("mode", mode)
            }
        else:
            return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/list")
async def get_models_list(mode: Optional[str] = None):
    """
    获取模型列表

    Args:
        mode: 可选，筛选特定模式的模型 ('llm', 'embed', 'rerank')

    Returns:
        模型列表和当前模型
    """
    try:
        models = db_config.get_all_models(mode=mode)
        current = db_config.get_current_model(mode=mode or "llm") if mode else None

        # 更新所有模型的下载状态
        for model in models:
            db_config.check_and_update_download_status(model["id"])

        # 重新获取更新后的模型列表
        models = db_config.get_all_models(mode=mode)

        model_list = [
            {
                "id": m["id"],
                "name": m["model_name"],
                "path": m["model_path"],
                "is_downloaded": bool(m.get("is_downloaded", False)),
                "mode": m.get("mode", "llm")
            }
            for m in models
        ]

        current_model_info = None
        if current:
            current_model_info = {
                "id": current["id"],
                "name": current["model_name"],
                "path": current["model_path"],
                "is_downloaded": bool(current.get("is_downloaded", False)),
                "mode": current.get("mode", "llm")
            }

        return {
            "models": model_list,
            "current_model": current_model_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/models/load")
async def load_model(request: SelectModelRequest):
    """
    加载模型（下载 + 切换 + 启动服务器）

    Args:
        request: 包含 model_name, download_url (可选), mode (可选)

    Returns:
        操作结果
    """
    try:
        result = await model_selection_pipeline.select_model(
            model_name=request.model_name,
            download_url=request.download_url,
            mode=request.mode or "llm"
        )
        return result
    except Exception as e:
        logger.error(f"Model load failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/models/download")
async def download_model(request: DownloadModelRequest):
    """
    下载模型（仅下载，不切换）

    Args:
        request: 包含 url, filename (可选), mode (可选)

    Returns:
        下载状态
    """
    try:
        mode = request.mode or "llm"
        from src.config import get_model_dir

        # 获取模式对应的目录
        mode_dir = get_model_dir(mode)

        # 使用全局 model_downloader，临时切换目录
        original_dir = model_downloader.download_dir
        model_downloader.download_dir = mode_dir

        # 开始下载（异步）
        asyncio.create_task(
            model_downloader.download_model(
                url=request.url,
                filename=request.filename
            )
        )

        # 恢复原目录
        model_downloader.download_dir = original_dir

        return {
            "success": True,
            "url": request.url,
            "mode": mode,
            "message": "Download started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/download/status")
async def get_download_status(url: Optional[str] = None):
    """
    获取下载进度状态

    Args:
        url: 可选，指定 URL 的下载状态。如果不提供，返回所有下载状态

    Returns:
        下载状态信息
    """
    try:
        if url:
            # 获取特定 URL 的下载状态
            status = model_downloader.get_download_status(url)
            if status:
                return {
                    "success": True,
                    "download": status
                }
            else:
                return {
                    "success": False,
                    "message": "Download not found"
                }
        else:
            # 获取所有下载状态
            all_downloads = model_downloader.get_all_downloads()
            return {
                "success": True,
                "downloads": all_downloads
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/get_param")
async def get_model_parameters(mode: str = "llm"):
    """
    获取模型参数

    Args:
        mode: 模型模式 ('llm', 'embed', 'rerank')

    Returns:
        模型参数配置
    """
    try:
        if mode == "llm":
            server = server_manager.get_server("llm")
            client = server_manager.get_client("llm")

            return {
                # LLMServer 参数
                "context_size": server.context_size,
                "threads": server.threads,
                "gpu_layers": server.gpu_layers,
                "batch_size": server.batch_size,
                # LLMClient 参数
                "temperature": client.temperature,
                "repeat_penalty": client.repeat_penalty,
                "max_tokens": client.max_tokens
            }
        elif mode == "embed":
            server = server_manager.get_server("embed")
            client = server_manager.get_client("embed")

            return {
                # EmbedServer 参数
                "context_size": server.context_size,
                "threads": server.threads,
                "gpu_layers": server.gpu_layers,
                "batch_size": server.batch_size,
                # EmbedClient 参数
                "normalize": client.normalize,
                "truncate": client.truncate
            }
        elif mode == "rerank":
            server = server_manager.get_server("rerank")
            client = server_manager.get_client("rerank")

            return {
                # RerankServer 参数
                "context_size": server.context_size,
                "threads": server.threads,
                "gpu_layers": server.gpu_layers,
                "batch_size": server.batch_size,
                # RerankClient 参数
                "top_n": client.top_n,
                "return_documents": client.return_documents
            }
        else:
            raise HTTPException(status_code=400, detail=f"Invalid mode: {mode}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/models/update_param")
async def update_model_parameters(request: Dict[str, Any], mode: str = "llm"):
    """
    更新模型参数

    Args:
        request: 参数字典
        mode: 模型模式 ('llm', 'embed', 'rerank')

    Returns:
        更新结果
    """
    try:
        if mode == "llm":
            # 使用现有的 parameter change pipeline
            result = await param_change_pipeline.apply_parameters(
                context_size=request.get("context_size"),
                threads=request.get("threads"),
                gpu_layers=request.get("gpu_layers"),
                batch_size=request.get("batch_size"),
                temperature=request.get("temperature"),
                repeat_penalty=request.get("repeat_penalty"),
                max_tokens=request.get("max_tokens")
            )
            return result
        elif mode == "embed":
            server = server_manager.get_server("embed")
            client = server_manager.get_client("embed")

            # 更新服务器参数
            server_params_changed = False
            if any(k in request for k in ["context_size", "threads", "gpu_layers", "batch_size"]):
                await server.update_params(
                    context_size=request.get("context_size"),
                    threads=request.get("threads"),
                    gpu_layers=request.get("gpu_layers"),
                    batch_size=request.get("batch_size")
                )
                server_params_changed = True

            # 更新客户端参数
            if any(k in request for k in ["normalize", "truncate"]):
                client.update_parameters(
                    normalize=request.get("normalize"),
                    truncate=request.get("truncate")
                )

            return {
                "success": True,
                "message": "Parameters updated successfully",
                "requires_restart": server_params_changed
            }
        elif mode == "rerank":
            server = server_manager.get_server("rerank")
            client = server_manager.get_client("rerank")

            # 更新服务器参数
            server_params_changed = False
            if any(k in request for k in ["context_size", "threads", "gpu_layers", "batch_size"]):
                await server.update_params(
                    context_size=request.get("context_size"),
                    threads=request.get("threads"),
                    gpu_layers=request.get("gpu_layers"),
                    batch_size=request.get("batch_size")
                )
                server_params_changed = True

            # 更新客户端参数
            if any(k in request for k in ["top_n", "return_documents"]):
                client.update_parameters(
                    top_n=request.get("top_n"),
                    return_documents=request.get("return_documents")
                )

            return {
                "success": True,
                "message": "Parameters updated successfully",
                "requires_restart": server_params_changed
            }
        else:
            raise HTTPException(status_code=400, detail=f"Invalid mode: {mode}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update parameters: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 辅助 API 端点（保留用于兼容性和功能支持）
# ============================================================================

@app.get("/api/server/status")
async def get_server_status(mode: str = "llm"):
    """
    获取服务器状态

    Args:
        mode: 模型模式 ('llm', 'embed', 'rerank')
    """
    try:
        server = server_manager.get_server(mode)
        status = server.get_status()
        return status
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/downloads/default-urls")
async def get_default_download_urls():
    """获取默认模型下载 URLs"""
    return {
        "urls": config.DEFAULT_MODEL_DOWNLOAD_URLS,
        "browser_path": config.DEFAULT_MODEL_BROWSER_PATH
    }


# ==================== Session Management APIs ====================

@app.post("/api/sessions", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest):
    """
    创建新会话

    Args:
        request: 包含用户第一条消息

    Returns:
        新会话的 ID 和名称
    """
    try:
        session_id = db_session.create_session(request.first_message)
        session = db_session.get_session(session_id)

        return CreateSessionResponse(
            session_id=session_id,
            session_name=session['session_name']
        )
    except Exception as e:
        logger.error(f"Failed to create session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions", response_model=SessionListResponse)
async def get_sessions(limit: int = 100, offset: int = 0):
    """
    获取会话列表，按更新时间倒序排列

    Args:
        limit: 返回的最大会话数
        offset: 偏移量（用于分页）

    Returns:
        会话列表
    """
    try:
        sessions = db_session.get_all_sessions(limit=limit, offset=offset)

        return SessionListResponse(
            sessions=[SessionInfo(**s) for s in sessions],
            total=len(sessions)
        )
    except Exception as e:
        logger.error(f"Failed to get sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: int):
    """
    获取会话详情

    Args:
        session_id: 会话 ID

    Returns:
        会话信息
    """
    try:
        session = db_session.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return SessionInfo(**session)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/sessions/{session_id}/name")
async def update_session_name(session_id: int, request: UpdateSessionNameRequest):
    """
    更新会话名称

    Args:
        session_id: 会话 ID
        request: 包含新的会话名称

    Returns:
        成功状态
    """
    try:
        success = db_session.update_session_name(session_id, request.new_name)

        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"success": True, "message": "Session name updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update session name: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: int):
    """
    删除会话（会级联删除所有消息）

    Args:
        session_id: 会话 ID

    Returns:
        成功状态
    """
    try:
        success = db_session.delete_session(session_id)

        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"success": True, "message": "Session deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/messages", response_model=MessagesResponse)
async def get_messages(session_id: int, limit: Optional[int] = None):
    """
    获取会话的消息列表

    Args:
        session_id: 会话 ID
        limit: 可选，限制返回的消息数量（最新的 N 条）

    Returns:
        消息列表
    """
    try:
        messages = db_session.get_messages(session_id, limit=limit)
        total_tokens = db_session.get_session_token_count(session_id)

        return MessagesResponse(
            messages=[MessageInfo(**m) for m in messages],
            session_id=session_id,
            total_tokens=total_tokens
        )
    except Exception as e:
        logger.error(f"Failed to get messages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions/{session_id}/messages", response_model=AddMessageResponse)
async def add_message(session_id: int, request: AddMessageRequest):
    """
    添加消息到会话

    Args:
        session_id: 会话 ID
        request: 包含角色和内容

    Returns:
        新消息的 ID 和 token 数
    """
    try:
        # 验证会话是否存在
        session = db_session.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # 估算 token 数
        token_count = estimate_message_tokens(request.role, request.content)

        # 添加消息
        message_id = db_session.add_message(
            session_id=session_id,
            role=request.role,
            content=request.content,
            token_count=token_count
        )

        return AddMessageResponse(
            message_id=message_id,
            token_count=token_count
        )
    except HTTPException:
        raise
    except ValueError as e:
        # 角色验证失败
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/sessions/{session_id}/messages")
async def clear_messages(session_id: int):
    """
    清空会话的所有消息

    Args:
        session_id: 会话 ID

    Returns:
        成功状态
    """
    try:
        success = db_session.clear_session_messages(session_id)

        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"success": True, "message": "Messages cleared"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear messages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    聊天接口（流式响应）

    支持两种模式：
    1. 无会话模式（session_id=None）：直接发送消息，不保存历史
    2. 会话模式（session_id提供）：加载历史记录，保存消息到数据库

    Args:
        request: 包含 messages, mode (可选), temperature (可选), session_id (可选) 等
    """
    try:
        mode = request.mode or "llm"

        # 获取对应模式的服务器和客户端
        server = server_manager.get_server(mode)
        client = server_manager.get_client(mode)

        # 检查服务器是否运行
        status = server.get_status()
        if not status["is_running"]:
            raise HTTPException(
                status_code=400,
                detail=f"{mode.upper()} server is not running. Please select a model first."
            )

        # 准备发送给 LLM 的消息列表
        messages_to_send = []

        # 会话模式：加载历史记录
        if request.session_id is not None:
            # 验证会话是否存在
            session = db_session.get_session(request.session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            # 获取系统提示词
            system_prompt_param = db_config.get_parameter("system_prompt")
            system_prompt = system_prompt_param if system_prompt_param else config.DEFAULT_SYSTEM_PROMPT

            # 估算系统提示词的 token 数
            system_prompt_tokens = estimate_message_tokens("system", system_prompt)

            # 获取 context_size 参数
            context_size_param = db_config.get_parameter("context_size")
            context_size = context_size_param if context_size_param else config.LLM_SERVER_CONTEXT_SIZE

            # 计算历史记录的最大 token 数（context_size 的一半）
            max_history_tokens = context_size // 2

            # 从数据库加载历史消息（在 token 限制内）
            history_messages = db_session.get_messages_within_token_limit(
                session_id=request.session_id,
                max_tokens=max_history_tokens,
                system_prompt_tokens=system_prompt_tokens
            )

            # 构建消息列表：[system] + [history] + [new_user_message]
            messages_to_send.append({"role": "system", "content": system_prompt})

            # 添加历史消息
            for msg in history_messages:
                messages_to_send.append({"role": msg["role"], "content": msg["content"]})

            # 添加新的用户消息（只取最后一条，因为前端可能发送多条）
            if request.messages:
                new_user_message = request.messages[-1]
                messages_to_send.append({"role": new_user_message.role, "content": new_user_message.content})

                # 保存用户消息到数据库
                user_token_count = estimate_message_tokens(new_user_message.role, new_user_message.content)
                db_session.add_message(
                    session_id=request.session_id,
                    role=new_user_message.role,
                    content=new_user_message.content,
                    token_count=user_token_count
                )
        else:
            # 无会话模式：直接使用请求中的消息
            messages_to_send = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        # 流式响应
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
                    # 收集助手响应内容
                    if "content" in chunk:
                        assistant_response += chunk["content"]

                    yield f"data: {json.dumps(chunk)}\n\n"

                yield "data: [DONE]\n\n"

                # 如果是会话模式，保存助手响应到数据库
                if request.session_id is not None and assistant_response:
                    assistant_token_count = estimate_message_tokens("assistant", assistant_response)
                    db_session.add_message(
                        session_id=request.session_id,
                        role="assistant",
                        content=assistant_response,
                        token_count=assistant_token_count
                    )

            except Exception as e:
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.API_SERVER_HOST, port=config.API_SERVER_PORT)
