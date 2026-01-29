# -*- coding: utf-8 -*-
"""
Zenow Backend Main Application
使用 APIRouter 重构后的主应用文件
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 导入所有路由
from routers import (
    models_router,
    sessions_router,
    chat_router,
    system_router,
    kb_router
)
from routers.knowledge_base import set_dependencies as set_kb_dependencies

# 导入核心组件
from spacemit_llm.model.server_manager import ModelServerManager
from spacemit_llm.model.download import ModelDownloader
from spacemit_llm.comon.sqlite.sqlite_config import SQLiteConfig
from spacemit_llm.comon.sqlite.sqlite_session import SQLiteSession
from spacemit_llm.comon.sqlite.sqlit_kb import SQLiteKnowledgeBase
from spacemit_llm.comon.minio import MinioServer, MinioClient
from spacemit_llm.pipeline.model_select import ModelSelectionPipeline
from spacemit_llm.pipeline.backend_start import BackendStartupHandler
from spacemit_llm.pipeline.model_param_change import ModelParameterChangePipeline
from spacemit_llm.pipeline.chat import ChatPipeline
from utils.port import write_port_file, cleanup_port_file
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# 全局组件初始化
# ============================================================================

# 数据库
db_config = SQLiteConfig(config.DB_CONFIG_PATH)
db_session = SQLiteSession(config.DB_SESSION_PATH)
db_kb = SQLiteKnowledgeBase()

# MinIO 服务
minio_server = MinioServer()
minio_client = None  # Will be initialized in startup event

# 模型服务器管理
server_manager = ModelServerManager()

# 模型下载器
model_downloader = ModelDownloader(config.LLM_MODELS_DIR)

# Pipeline 组件
model_selection_pipeline = ModelSelectionPipeline(
    models_dir=config.LLM_MODELS_DIR,
    downloader=model_downloader,
    server_manager=server_manager,
    db_config=db_config
)

# Register startup handler to initialize database and start all current models
startup_handler = BackendStartupHandler(server_manager, db_config, config)

# Register parameter change pipeline
param_change_pipeline = ModelParameterChangePipeline(
    server_manager.get_server("llm"),
    server_manager.get_client("llm"),
    db_config
)

# Initialize chat pipeline
chat_pipeline = ChatPipeline(
    server_manager,
    db_config,
    db_session,
    default_system_prompt=config.DEFAULT_SYSTEM_PROMPT,
    default_context_size=config.LLM_SERVER_CONTEXT_SIZE
)

# ============================================================================
# 设置路由依赖
# ============================================================================

# 设置 models router 的全局变量
models_router.server_manager = server_manager
models_router.model_downloader = model_downloader
models_router.db_config = db_config
models_router.model_selection_pipeline = model_selection_pipeline
models_router.param_change_pipeline = param_change_pipeline

# 设置 sessions router 的全局变量
sessions_router.db_session = db_session

# 设置 chat router 的全局变量
chat_router.chat_pipeline = chat_pipeline

# 知识库路由的依赖将在 startup 事件中设置（MinIO 客户端初始化后）

# ============================================================================
# FastAPI 应用配置
# ============================================================================

app = FastAPI(
    title="Zenow API",
    description="Zenow LLM Chat Application API",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册所有路由
app.include_router(system_router)    # 系统路由（包含根路径和健康检查）
app.include_router(models_router)    # 模型管理路由
app.include_router(sessions_router)  # 会话管理路由
app.include_router(chat_router)      # 聊天路由
app.include_router(kb_router)        # 知识库管理路由

# ============================================================================
# 应用生命周期事件
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    global minio_client
    logger.info("🚀 Starting Zenow Backend...")

    # 启动 MinIO 服务
    try:
        if minio_server.start():
            logger.info("✅ MinIO server started")
            # 初始化 MinIO 客户端
            try:
                minio_client = MinioClient()
                # 更新知识库路由的依赖
                set_kb_dependencies(db_kb, minio_client)
                logger.info("✅ MinIO client initialized")
            except Exception as e:
                logger.warning(f"⚠️ MinIO client initialization failed: {e}, continuing without file storage")
        else:
            logger.warning("⚠️ MinIO server failed to start, continuing without file storage")
    except Exception as e:
        logger.warning(f"⚠️ MinIO startup error: {e}, continuing without file storage")

    # 写入端口文件
    write_port_file(config.API_SERVER_PORT)

    # 初始化数据库和启动模型
    await startup_handler.initialize()

    logger.info("✅ Zenow Backend started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    logger.info("🛑 Shutting down Zenow Backend...")

    # 停止所有 llama-server 进程
    try:
        await server_manager.stop_all()
        logger.info("✓ All llama-server processes stopped")
    except Exception as e:
        logger.warning(f"Async cleanup failed: {e}, trying synchronous cleanup")
        server_manager.stop_all_sync()
        logger.info("✓ All llama-server processes stopped (sync)")

    # 停止 MinIO 服务
    try:
        minio_server.stop()
        logger.info("✓ MinIO server stopped")
    except Exception as e:
        logger.warning(f"MinIO shutdown error: {e}")

    # 清理端口文件
    cleanup_port_file()

    logger.info("✅ Zenow Backend shutdown complete")

# ============================================================================
# 应用启动
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.API_SERVER_HOST, port=config.API_SERVER_PORT)