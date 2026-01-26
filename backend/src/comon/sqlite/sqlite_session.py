"""
SQLite session management for chat history
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from .sqlite_base import SQLiteBase


class SQLiteSession(SQLiteBase):
    """SQLite database class for chat session management"""

    def __init__(self, db_path: Path):
        """Initialize session database"""
        super().__init__(db_path)

    def _init_db(self):
        """初始化会话表"""
        # 会话表
        self.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_count INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0
            )
        """)

        # 消息表
        self.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                token_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)

        # 创建索引以提高查询性能
        self.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_updated_at
            ON sessions(updated_at DESC)
        """)

        self.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session_id
            ON messages(session_id, created_at ASC)
        """)

    # ==================== Session Management ====================

    def create_session(self, first_user_message: str, max_name_length: int = 12) -> int:
        """
        创建新会话，会话名从用户第一条消息中提取

        Args:
            first_user_message: 用户的第一条消息
            max_name_length: 会话名最大长度（字符数，默认12）

        Returns:
            新会话的 ID
        """
        # 从用户消息中提取会话名（取前 N 个字符）
        session_name = first_user_message[:max_name_length]
        if len(first_user_message) > max_name_length:
            session_name += "..."

        cursor = self.execute(
            "INSERT INTO sessions (session_name) VALUES (?)",
            (session_name,)
        )
        return cursor.lastrowid

    def get_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        return self.fetchone(
            "SELECT * FROM sessions WHERE id = ?",
            (session_id,)
        )

    def get_all_sessions(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取所有会话，按更新时间倒序排列

        Args:
            limit: 返回的最大会话数
            offset: 偏移量（用于分页）

        Returns:
            会话列表
        """
        return self.fetchall(
            """
            SELECT
                id,
                session_name,
                created_at,
                updated_at,
                message_count,
                total_tokens
            FROM sessions
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        )

    def update_session_name(self, session_id: int, new_name: str) -> bool:
        """
        更新会话名称

        Args:
            session_id: 会话 ID
            new_name: 新的会话名称

        Returns:
            是否成功
        """
        self.execute(
            """
            UPDATE sessions
            SET session_name = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_name, session_id)
        )
        return True

    def delete_session(self, session_id: int) -> bool:
        """
        删除会话（会级联删除所有消息）

        Args:
            session_id: 会话 ID

        Returns:
            是否成功
        """
        self.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        return True

    def update_session_stats(self, session_id: int) -> bool:
        """
        更新会话统计信息（消息数量、总 token 数、更新时间）

        Args:
            session_id: 会话 ID

        Returns:
            是否成功
        """
        self.execute(
            """
            UPDATE sessions
            SET
                message_count = (
                    SELECT COUNT(*) FROM messages WHERE session_id = ?
                ),
                total_tokens = (
                    SELECT COALESCE(SUM(token_count), 0) FROM messages WHERE session_id = ?
                ),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (session_id, session_id, session_id)
        )
        return True

    # ==================== Message Management ====================

    def add_message(
        self,
        session_id: int,
        role: str,
        content: str,
        token_count: int
    ) -> int:
        """
        添加消息到会话（仅支持 user 和 assistant）

        Args:
            session_id: 会话 ID
            role: 角色 ('user' 或 'assistant')
            content: 消息内容
            token_count: 预估的 token 数量

        Returns:
            新消息的 ID

        Raises:
            ValueError: 如果 role 不是 'user' 或 'assistant'
        """
        # 验证角色
        if role not in ['user', 'assistant']:
            raise ValueError(f"Invalid role: {role}. Only 'user' and 'assistant' are allowed.")

        cursor = self.execute(
            """
            INSERT INTO messages (session_id, role, content, token_count)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, role, content, token_count)
        )

        message_id = cursor.lastrowid

        # 更新会话统计信息
        self.update_session_stats(session_id)

        return message_id

    def get_messages(
        self,
        session_id: int,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取会话的所有消息，按时间正序排列

        Args:
            session_id: 会话 ID
            limit: 可选，限制返回的消息数量（最新的 N 条）

        Returns:
            消息列表
        """
        if limit:
            # 获取最新的 N 条消息
            query = """
                SELECT * FROM (
                    SELECT
                        id,
                        session_id,
                        role,
                        content,
                        token_count,
                        created_at
                    FROM messages
                    WHERE session_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ) ORDER BY created_at ASC
            """
            return self.fetchall(query, (session_id, limit))
        else:
            # 获取所有消息
            query = """
                SELECT
                    id,
                    session_id,
                    role,
                    content,
                    token_count,
                    created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY created_at ASC
            """
            return self.fetchall(query, (session_id,))

    def get_messages_within_token_limit(
        self,
        session_id: int,
        max_tokens: int,
        system_prompt_tokens: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取会话消息，确保总 token 数不超过限制
        从最新的消息开始往前取，保证会话历史的完整性（成对的 user-assistant）

        Args:
            session_id: 会话 ID
            max_tokens: 最大 token 数（通常是 context_size 的一半）
            system_prompt_tokens: 系统提示词的 token 数

        Returns:
            消息列表（按时间正序）
        """
        # 获取所有消息（倒序）
        all_messages = self.fetchall(
            """
            SELECT
                id,
                session_id,
                role,
                content,
                token_count,
                created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY created_at DESC
            """,
            (session_id,)
        )

        if not all_messages:
            return []

        # 计算可用的 token 数（减去系统提示词）
        available_tokens = max_tokens - system_prompt_tokens

        selected_messages = []
        current_tokens = 0

        # 从最新的消息开始往前取
        for msg in all_messages:
            msg_tokens = msg['token_count']

            # 检查是否超过限制
            if current_tokens + msg_tokens > available_tokens:
                break

            selected_messages.append(msg)
            current_tokens += msg_tokens

        # 反转列表，使其按时间正序
        selected_messages.reverse()

        return selected_messages

    def delete_message(self, message_id: int) -> bool:
        """
        删除消息

        Args:
            message_id: 消息 ID

        Returns:
            是否成功
        """
        # 先获取 session_id
        message = self.fetchone(
            "SELECT session_id FROM messages WHERE id = ?",
            (message_id,)
        )

        if not message:
            return False

        session_id = message['session_id']

        # 删除消息
        self.execute("DELETE FROM messages WHERE id = ?", (message_id,))

        # 更新会话统计信息
        self.update_session_stats(session_id)

        return True

    def clear_session_messages(self, session_id: int) -> bool:
        """
        清空会话的所有消息

        Args:
            session_id: 会话 ID

        Returns:
            是否成功
        """
        self.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        self.update_session_stats(session_id)
        return True

    # ==================== Statistics ====================

    def get_session_token_count(self, session_id: int) -> int:
        """
        获取会话的总 token 数

        Args:
            session_id: 会话 ID

        Returns:
            总 token 数
        """
        result = self.fetchone(
            "SELECT COALESCE(SUM(token_count), 0) as total FROM messages WHERE session_id = ?",
            (session_id,)
        )
        return result['total'] if result else 0

    def get_session_message_count(self, session_id: int) -> int:
        """
        获取会话的消息数量

        Args:
            session_id: 会话 ID

        Returns:
            消息数量
        """
        result = self.fetchone(
            "SELECT COUNT(*) as count FROM messages WHERE session_id = ?",
            (session_id,)
        )
        return result['count'] if result else 0
