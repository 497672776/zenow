"""
SQLite 数据库基类，用于 Zenow 后端
"""
import sqlite3
from pathlib import Path
from typing import Optional, Any, List, Dict
import threading


class SQLiteBase:
    """SQLite 数据库操作基类"""

    def __init__(self, db_path: Path):
        """
        初始化 SQLite 数据库连接

        Args:
            db_path: SQLite 数据库文件路径
        """
        self.db_path = db_path
        self._local = threading.local()
        self._init_db()

    @property
    def conn(self) -> sqlite3.Connection:
        """获取线程本地数据库连接"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self):
        """初始化数据库模式 - 由子类实现"""
        pass

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        执行 SQL 查询

        Args:
            query: SQL 查询字符串
            params: 查询参数

        Returns:
            游标对象
        """
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor

    def fetchone(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """
        从查询中获取一行数据

        Args:
            query: SQL 查询字符串
            params: 查询参数

        Returns:
            行数据字典，如果没有则返回 None
        """
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def fetchall(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        从查询中获取所有行数据

        Args:
            query: SQL 查询字符串
            params: 查询参数

        Returns:
            包含行数据的字典列表
        """
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def close(self):
        """关闭数据库连接"""
        if hasattr(self._local, 'conn') and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None

    def __del__(self):
        """析构函数，确保连接被关闭"""
        self.close()
