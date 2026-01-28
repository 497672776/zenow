"""
System API Router
处理系统相关的接口
"""

from fastapi import APIRouter
import config

router = APIRouter(tags=["system"])


@router.get("/")
async def root():
    """
    根路径接口

    Returns:
        API 基本信息
    """
    return {"message": "Zenow LLM Chat API"}


@router.get("/api/health")
async def health_check():
    """
    健康检查端点

    Returns:
        简单的健康状态响应
    """
    return {"status": "healthy", "app": "zenow"}

