"""
Chat API Router
处理聊天相关的接口
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api", tags=["chat"])

# ==================== Chat Models ====================

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: Message
    stream: Optional[bool] = False
    temperature: Optional[float] = None
    repeat_penalty: Optional[float] = None
    max_tokens: Optional[int] = None
    mode: Optional[str] = "llm"  # Added mode parameter
    session_id: Optional[int] = None  # Optional session ID for history management

# ==================== Dependency Injection ====================

chat_pipeline = None

# ==================== Chat Endpoints ====================

@router.post("/chat")
async def chat(request: ChatRequest):
    """
    聊天接口（流式响应）

    必须提供 session_id，所有聊天都会保存到数据库

    Args:
        request: 包含 message, mode (可选), temperature (可选), session_id (必需) 等
    """
    return await router.chat_pipeline.process_chat(request)