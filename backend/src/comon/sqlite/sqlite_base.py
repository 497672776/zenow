"""
SQLite database base class for Zenow backend
"""
import sqlite3
from pathlib import Path
from typing import Optional, Any, List, Dict
import threading


class SQLiteBase:
    """Base class for SQLite database operations"""

    def __init__(self, db_path: Path):
        """
        Initialize SQLite database connection

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._local = threading.local()
        self._init_db()

    @property
    def conn(self) -> sqlite3.Connection:
        """Get thread-local database connection"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self):
        """Initialize database schema - to be implemented by subclasses"""
        pass

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Execute a SQL query

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Cursor object
        """
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor

    def fetchone(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """
        Fetch one row from query

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Dictionary of row data or None
        """
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def fetchall(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Fetch all rows from query

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of dictionaries containing row data
        """
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def close(self):
        """Close database connection"""
        if hasattr(self._local, 'conn') and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None

    def __del__(self):
        """Destructor to ensure connection is closed"""
        self.close()
