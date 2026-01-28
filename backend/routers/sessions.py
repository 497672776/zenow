"""
Sessions API Router
处理会话相关的所有接口
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

# 导入必要的依赖
from spacemit_llm.comon.sqlite.sqlite_session import SQLiteSession
from spacemit_llm.utils.token_estimator import estimate_message_tokens

logger = logging.getLogger(__name__)

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
    session_id: int

# ==================== Router Definition ====================

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

# 依赖注入 - 这些需要在 main.py 中配置
db_session = None

# ==================== Session Endpoints ====================

@router.post("", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest, ):
    """
    创建新会话

    Args:
        request: 包含第一条消息的请求

    Returns:
        新创建的会话信息
    """
    try:
        # 创建会话并获取会话ID
        session_id = router.db_session.create_session(request.first_message)

        # 获取会话信息以返回会话名
        session = router.db_session.get_session(session_id)
        if not session:
            raise HTTPException(status_code=500, detail="Failed to retrieve created session")

        logger.info(f"Created new session: {session_id}")

        return CreateSessionResponse(
            session_id=session_id,
            session_name=session["session_name"]
        )
    except Exception as e:
        logger.error(f"Failed to create session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    limit: int = 50,
    offset: int = 0,
    
):
    """
    获取会话列表

    Args:
        limit: 返回的会话数量限制
        offset: 偏移量

    Returns:
        会话列表和总数
    """
    try:
        sessions_data = router.db_session.get_all_sessions(limit=limit, offset=offset)
        sessions = [
            SessionInfo(
                id=session["id"],
                session_name=session["session_name"],
                created_at=session["created_at"],
                updated_at=session["updated_at"],
                message_count=session["message_count"],
                total_tokens=session["total_tokens"]
            )
            for session in sessions_data
        ]

        return SessionListResponse(
            sessions=sessions,
            total=len(sessions_data)
        )
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}")
async def get_session(session_id: int, ):
    """
    获取会话详情

    Args:
        session_id: 会话ID

    Returns:
        会话详细信息
    """
    try:
        session = router.db_session.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return SessionInfo(
            id=session["id"],
            session_name=session["session_name"],
            created_at=session["created_at"],
            updated_at=session["updated_at"],
            message_count=session["message_count"],
            total_tokens=session["total_tokens"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{session_id}/name")
async def update_session_name(
    session_id: int,
    request: UpdateSessionNameRequest,
    
):
    """
    更新会话名称

    Args:
        session_id: 会话ID
        request: 包含新名称的请求

    Returns:
        更新结果
    """
    try:
        # 检查会话是否存在
        session = router.db_session.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # 更新会话名称
        success = router.db_session.update_session_name(session_id, request.new_name)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update session name")

        logger.info(f"Updated session {session_id} name to: {request.new_name}")

        return {"success": True, "message": "Session name updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update session name: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}")
async def delete_session(session_id: int, ):
    """
    删除会话

    Args:
        session_id: 会话ID

    Returns:
        删除结果
    """
    try:
        # 检查会话是否存在
        session = router.db_session.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # 删除会话（级联删除消息）
        success = router.db_session.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete session")

        logger.info(f"Deleted session: {session_id}")

        return {"success": True, "message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/messages", response_model=MessagesResponse)
async def get_session_messages(
    session_id: int,
    limit: int = 100,
    
):
    """
    获取会话消息

    Args:
        session_id: 会话ID
        limit: 消息数量限制

    Returns:
        消息列表和统计信息
    """
    try:
        # 检查会话是否存在
        session = router.db_session.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # 获取消息列表
        messages_data = router.db_session.get_messages(session_id, limit=limit)
        messages = [
            MessageInfo(
                id=msg["id"],
                session_id=msg["session_id"],
                role=msg["role"],
                content=msg["content"],
                token_count=msg["token_count"],
                created_at=msg["created_at"]
            )
            for msg in messages_data
        ]

        # 计算总token数
        total_tokens = sum(msg.token_count for msg in messages)

        return MessagesResponse(
            messages=messages,
            session_id=session_id,
            total_tokens=total_tokens
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get messages for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/messages", response_model=AddMessageResponse)
async def add_message(
    session_id: int,
    request: AddMessageRequest,
    
):
    """
    添加消息到会话

    Args:
        session_id: 会话ID
        request: 消息内容

    Returns:
        添加的消息信息
    """
    try:
        # 检查会话是否存在
        session = router.db_session.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # 估算token数
        token_count = estimate_message_tokens(request.role, request.content)

        # 添加消息
        message_id = router.db_session.add_message(
            session_id=session_id,
            role=request.role,
            content=request.content,
            token_count=token_count
        )

        logger.info(f"Added message to session {session_id}, message_id: {message_id}")

        return AddMessageResponse(
            message_id=message_id,
            session_id=session_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}/messages")
async def clear_session_messages(session_id: int, ):
    """
    清空会话消息

    Args:
        session_id: 会话ID

    Returns:
        清空结果
    """
    try:
        # 检查会话是否存在
        session = router.db_session.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # 清空消息
        success = router.db_session.clear_session_messages(session_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to clear messages")

        logger.info(f"Cleared messages for session: {session_id}")

        return {"success": True, "message": "Messages cleared successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear messages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))