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
from src.model.download import ModelDownloader
from src.comon.sqlite.sqlite_config import SQLiteConfig
from src.pipeline.model_select import ModelSelectionPipeline
from src.pipeline.backend_exit import BackendExitHandler
from src.pipeline.backend_start import BackendStartupHandler
from src.pipeline.model_param_change import ModelParameterChangePipeline
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
llm_server = LLMServer(
    host=config.LLM_SERVER_HOST,
    port=config.LLM_SERVER_PORT,
    context_size=config.LLM_SERVER_CONTEXT_SIZE,
    threads=config.LLM_SERVER_THREADS,
    gpu_layers=config.LLM_SERVER_GPU_LAYERS,
    batch_size=config.LLM_SERVER_BATCH_SIZE
)
llm_client = LLMClient(
    base_url=config.LLM_CLIENT_BASE_URL,
    temperature=config.LLM_CLIENT_TEMPERATURE,
    repeat_penalty=config.LLM_CLIENT_REPEAT_PENALTY,
    max_tokens=config.LLM_CLIENT_MAX_TOKENS
)
model_downloader = ModelDownloader(config.MODELS_DIR)
model_selection_pipeline = ModelSelectionPipeline(
    models_dir=config.MODELS_DIR,
    downloader=model_downloader,
    llm_server=llm_server,
    db_config=db_config
)

# Register exit handler to clean up llama-server on backend exit
exit_handler = BackendExitHandler(llm_server)
exit_handler.register()

# Register startup handler to initialize database and start model
startup_handler = BackendStartupHandler(llm_server, llm_client, db_config, config)

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

class ChatResponse(BaseModel):
    message: Message
    model: str

class ModelInfo(BaseModel):
    id: int
    name: str
    path: str
    is_downloaded: bool

class ModelListResponse(BaseModel):
    models: List[ModelInfo]
    current_model: Optional[ModelInfo] = None

class AddModelRequest(BaseModel):
    name: str
    path: str

class ServerStatusResponse(BaseModel):
    status: str
    model_name: Optional[str] = None
    model_path: Optional[str] = None
    is_running: bool
    error_message: Optional[str] = None

class DownloadModelRequest(BaseModel):
    url: str
    filename: Optional[str] = None

class DownloadStatusResponse(BaseModel):
    url: str
    filename: str
    status: str  # downloading, completed, failed
    downloaded: int
    total: int
    progress: float
    error: Optional[str] = None

class DefaultDownloadUrlsResponse(BaseModel):
    urls: List[str]
    browser_path: str

class SelectModelRequest(BaseModel):
    model_name: str
    download_url: Optional[str] = None

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


@app.get("/")
async def root():
    return {"message": "Zenow LLM Chat API"}


@app.get("/api/models", response_model=ModelListResponse)
async def get_models():
    """Get list of available models and current model"""
    try:
        models = db_config.get_all_models()
        current = db_config.get_current_model()

        model_list = [
            ModelInfo(
                id=m["id"],
                name=m["model_name"],
                path=m["model_path"],
                is_downloaded=bool(m.get("is_downloaded", False))
            )
            for m in models
        ]

        current_model_info = None
        if current:
            current_model_info = ModelInfo(
                id=current["id"],
                name=current["model_name"],
                path=current["model_path"],
                is_downloaded=bool(current.get("is_downloaded", False))
            )

        return ModelListResponse(
            models=model_list,
            current_model=current_model_info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/models/add")
async def add_model(request: AddModelRequest):
    """Add a new model to the database"""
    try:
        model_id = db_config.add_model(request.name, request.path)
        return {"success": True, "model_id": model_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/models/current")
async def set_current_model(model_id: int):
    """Set the current model"""
    try:
        success = db_config.set_current_model(model_id)
        if success:
            return {"success": True, "model_id": model_id}
        else:
            raise HTTPException(status_code=404, detail="Model not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/current")
async def get_current_model():
    """Get the current model"""
    try:
        current = db_config.get_current_model()
        if current:
            return ModelInfo(
                id=current["id"],
                name=current["model_name"],
                path=current["model_path"],
                status=current["status"]
            )
        else:
            return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/server/start")
async def start_server():
    """Start the LLM server with current model"""
    try:
        current_model = db_config.get_current_model()
        if not current_model:
            raise HTTPException(status_code=400, detail="No current model set")

        success = llm_server.start_server(
            model_path=current_model["model_path"],
            model_name=current_model["model_name"]
        )

        if success:
            return {"success": True, "model": current_model["model_name"]}
        else:
            raise HTTPException(status_code=500, detail="Failed to start server")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/server/stop")
async def stop_server():
    """Stop the LLM server"""
    try:
        success = llm_server.stop_server()
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/server/status", response_model=ServerStatusResponse)
async def get_server_status():
    """Get the LLM server status"""
    try:
        status = llm_server.get_status()
        return ServerStatusResponse(**status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/server/switch")
async def switch_model(model_id: int):
    """Switch to a different model"""
    try:
        # Get model from database
        models = db_config.get_all_models()
        target_model = None
        for m in models:
            if m["id"] == model_id:
                target_model = m
                break

        if not target_model:
            raise HTTPException(status_code=404, detail="Model not found")

        # Switch model (async)
        success = await llm_server.switch(
            model_path=target_model["model_path"],
            model_name=target_model["model_name"]
        )

        if success:
            db_config.set_current_model(model_id)
            return {"success": True, "model": target_model["model_name"]}
        else:
            raise HTTPException(status_code=500, detail="Failed to switch model")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/models/select", response_model=SelectModelResponse)
async def select_model(request: SelectModelRequest):
    """
    Select a model through the complete pipeline:
    1. Check if model exists in ~/.cache/zenow/model/
    2. If not, download it (if URL provided)
    3. Start/restart llama-server if needed
    4. Update database with current model
    """
    try:
        result = await model_selection_pipeline.select_model(
            model_name=request.model_name,
            download_url=request.download_url
        )
        return SelectModelResponse(**result)
    except Exception as e:
        logger.error(f"Model selection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Send a chat message and get a response"""
    try:
        # Check if server is running
        status = llm_server.get_status()
        if not status["is_running"]:
            raise HTTPException(status_code=400, detail="LLM server is not running")

        # Convert messages to dict format
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        # Always use streaming
        async def generate():
            try:
                stream_gen = llm_client.chat_stream(
                    messages=messages,
                    temperature=request.temperature,
                    repeat_penalty=request.repeat_penalty,
                    max_tokens=request.max_tokens
                )
                async for chunk in stream_gen:
                    # Send SSE formatted data
                    yield f"data: {json.dumps(chunk)}\n\n"

                # Send done signal
                yield "data: [DONE]\n\n"
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/downloads/default-urls", response_model=DefaultDownloadUrlsResponse)
async def get_default_download_urls():
    """Get default model download URLs and browser path"""
    return DefaultDownloadUrlsResponse(
        urls=config.DEFAULT_MODEL_DOWNLOAD_URLS,
        browser_path=config.DEFAULT_MODEL_BROWSER_PATH
    )


@app.post("/api/downloads/start")
async def start_download(request: DownloadModelRequest):
    """Start downloading a model"""
    try:
        # Start download in background
        asyncio.create_task(
            model_downloader.download_model(
                url=request.url,
                filename=request.filename
            )
        )
        return {"success": True, "url": request.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/downloads/status/{url:path}")
async def get_download_status(url: str):
    """Get download status for a specific URL"""
    status = model_downloader.get_download_status(url)
    if status is None:
        raise HTTPException(status_code=404, detail="Download not found")
    return status


@app.get("/api/downloads/all")
async def get_all_downloads():
    """Get status of all downloads"""
    return model_downloader.get_all_downloads()


@app.get("/api/parameters", response_model=LLMParametersResponse)
async def get_parameters():
    """获取当前 LLM 参数配置"""
    try:
        return LLMParametersResponse(
            # LLMServer 参数
            context_size=llm_server.context_size,
            threads=llm_server.threads,
            gpu_layers=llm_server.gpu_layers,
            batch_size=llm_server.batch_size,
            # LLMClient 参数
            temperature=llm_client.temperature,
            repeat_penalty=llm_client.repeat_penalty,
            max_tokens=llm_client.max_tokens
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/parameters", response_model=UpdateParametersResponse)
async def update_parameters(request: LLMParametersRequest):
    """
    更新 LLM 参数配置

    - LLMServer 参数（context_size, threads, gpu_layers, batch_size）需要重启服务
    - LLMClient 参数（temperature, repeat_penalty, max_tokens）立即生效
    """
    try:
        # 使用 pipeline 处理参数更新
        result = await param_change_pipeline.apply_parameters(
            context_size=request.context_size,
            threads=request.threads,
            gpu_layers=request.gpu_layers,
            batch_size=request.batch_size,
            temperature=request.temperature,
            repeat_penalty=request.repeat_penalty,
            max_tokens=request.max_tokens
        )

        return UpdateParametersResponse(
            success=result["success"],
            message=result["message"],
            requires_restart=result["requires_restart"]
        )
    except Exception as e:
        logger.error(f"Failed to update parameters: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.API_SERVER_HOST, port=config.API_SERVER_PORT)
