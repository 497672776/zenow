"""
Models API Router
处理模型相关的所有接口
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

# 导入必要的依赖
from spacemit_llm.model.server_manager import ModelServerManager
from spacemit_llm.model.download import ModelDownloader
from spacemit_llm.comon.sqlite.sqlite_config import SQLiteConfig
from spacemit_llm.pipeline.model_select import ModelSelectionPipeline
from spacemit_llm.pipeline.model_param_change import ModelParameterChangePipeline

logger = logging.getLogger(__name__)

# ==================== Models Management Models ====================

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

# ==================== Router Definition ====================

router = APIRouter(prefix="/api/models", tags=["models"])

# 全局变量，将在 main.py 中设置
server_manager = None
model_downloader = None
db_config = None
model_selection_pipeline = None
param_change_pipeline = None

# ==================== Models Endpoints ====================

@router.get("/current")
async def get_current_model(mode: str = "llm"):
    """
    获取当前模型

    Args:
        mode: 模型模式 ('llm', 'embed', 'rerank')
    """
    try:
        current_model = router.db_config.get_current_model(mode)
        if current_model:
            return ModelInfo(
                id=current_model["id"],
                name=current_model["model_name"],
                path=current_model["model_path"],
                is_downloaded=current_model["is_downloaded"],
                mode=current_model.get("mode", mode)
            )
        else:
            return {"message": f"No current {mode} model set"}
    except Exception as e:
        logger.error(f"Failed to get current {mode} model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_models(
    mode: str = "llm",
    
):
    """
    获取模型列表

    Args:
        mode: 模型模式 ('llm', 'embed', 'rerank')
    """
    try:
        models_data = router.db_config.get_all_models(mode)
        current_model_data = router.db_config.get_current_model(mode)

        models = [
            ModelInfo(
                id=model["id"],
                name=model["model_name"],
                path=model["model_path"],
                is_downloaded=model["is_downloaded"],
                mode=model.get("mode", mode)
            )
            for model in models_data
        ]

        current_model = None
        if current_model_data:
            current_model = ModelInfo(
                id=current_model_data["id"],
                name=current_model_data["model_name"],
                path=current_model_data["model_path"],
                is_downloaded=current_model_data["is_downloaded"],
                mode=current_model_data.get("mode", mode)
            )

        return ModelListResponse(
            models=models,
            current_model=current_model
        )
    except Exception as e:
        logger.error(f"Failed to list {mode} models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/load")
async def load_model(
    request: SelectModelRequest,
    
):
    """
    加载/切换模型
    """
    try:
        result = await router.model_selection_pipeline.select_model(
            model_name=request.model_name,
            download_url=request.download_url,
            mode=request.mode or "llm"
        )

        return SelectModelResponse(
            success=result["success"],
            message=result["message"],
            model_name=request.model_name,
            model_path=result.get("model_path"),
            server_status=result.get("server_status", "unknown")
        )
    except Exception as e:
        logger.error(f"Failed to load model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download")
async def download_model(
    request: DownloadModelRequest,
    
):
    """
    下载模型
    """
    try:
        result = await router.model_downloader.download_model(
            url=request.url,
            filename=request.filename,
            mode=request.mode or "llm"
        )

        return {
            "success": True,
            "message": "Download started",
            "url": request.url,
            "filename": result.get("filename", ""),
            "mode": request.mode or "llm"
        }
    except Exception as e:
        logger.error(f"Failed to start download: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/status")
async def get_download_status(
    url: Optional[str] = None,

):
    """
    获取下载状态

    Args:
        url: 可选，特定下载的URL。如果不提供，返回所有下载状态
    """
    try:
        if url:
            # 获取特定URL的下载状态
            status = router.model_downloader.get_download_status(url)
            if status:
                return DownloadStatusResponse(
                    url=status["url"],
                    filename=status["filename"],
                    status=status["status"],
                    downloaded=status["downloaded"],
                    total=status["total"],
                    progress=status["progress"],
                    error=status.get("error")
                )
            else:
                raise HTTPException(status_code=404, detail=f"Download not found for URL: {url}")
        else:
            # 返回所有下载状态
            all_downloads = router.model_downloader.get_all_downloads()
            return {
                "success": True,
                "downloads": all_downloads
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_param")
async def get_parameters(
    mode: str = "llm",
    
):
    """
    获取模型参数
    """
    try:
        if mode != "llm":
            raise HTTPException(status_code=400, detail="Parameters only available for LLM mode")

        # 获取所有参数
        params = {}
        param_names = [
            "context_size", "threads", "gpu_layers", "batch_size",
            "temperature", "repeat_penalty", "max_tokens"
        ]

        for param_name in param_names:
            value = router.db_config.get_parameter(param_name)
            if value is not None:
                params[param_name] = value

        return LLMParametersResponse(**params)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get parameters: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update_param")
async def update_parameters(
    request: LLMParametersRequest,
    mode: str = "llm",
    
):
    """
    更新模型参数
    """
    try:
        if mode != "llm":
            raise HTTPException(status_code=400, detail="Parameters only available for LLM mode")

        # 转换为字典，过滤掉 None 值
        params = {k: v for k, v in request.model_dump().items() if v is not None}

        if not params:
            raise HTTPException(status_code=400, detail="No parameters provided")

        result = await router.param_change_pipeline.apply_parameters(**params)

        return UpdateParametersResponse(
            success=result["success"],
            message=result["message"],
            requires_restart=result.get("requires_restart", False)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update parameters: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/server_status")
async def get_server_status(
    mode: str = "llm",

):
    """
    获取服务器状态

    Args:
        mode: 模型模式 ('llm', 'embed', 'rerank')
    """
    try:
        server = router.server_manager.get_server(mode)
        status = server.get_status()

        return ServerStatusResponse(
            status=status["status"],
            model_name=status.get("model_name"),
            model_path=status.get("model_path"),
            is_running=status["is_running"],
            error_message=status.get("error_message")
        )
    except Exception as e:
        logger.error(f"Failed to get {mode} server status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))