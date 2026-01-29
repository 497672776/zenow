"""
SQLite Knowledge Base Management Module

Manages knowledge base metadata and file information using SQLite.

Tables:
- knowledge_bases: Store KB metadata (name, description, created_at, updated_at)
- kb_files: Store file information (filename, file_path, file_size, file_type, uploaded_at)

Usage:
    db = SQLiteKnowledgeBase()

    # Create knowledge base
    kb_id = await db.create_knowledge_base("My KB", "Description")

    # Add file
    file_id = await db.add_file(kb_id, "document.pdf", "kb/doc.pdf", 1024, "pdf")

    # Get KB files
    files = await db.get_kb_files(kb_id)

    # Delete KB (cascades to files)
    await db.delete_knowledge_base(kb_id)
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class SQLiteKnowledgeBase:
    """SQLite Knowledge Base Management."""

    def __init__(self, db_path: str = None):
        """Initialize SQLite Knowledge Base manager.

        Args:
            db_path: Path to SQLite database file
                    (default: ~/.cache/zenow/data/db/knowledge_base.db)
        """
        if db_path is None:
            db_path = Path.home() / ".cache" / "zenow" / "data" / "db" / "knowledge_base.db"

        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()
        logger.info(f"✅ SQLite Knowledge Base initialized: {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database tables."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Create knowledge_bases table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_bases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    avatar_url TEXT,
                    doc_count INTEGER DEFAULT 0,
                    total_size INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create kb_files table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kb_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kb_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_type TEXT NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE,
                    UNIQUE(kb_id, filename)
                )
            """)

            conn.commit()
            logger.debug("✅ Database tables initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise
        finally:
            conn.close()

    async def create_knowledge_base(
        self,
        name: str,
        description: str = "",
        avatar_url: str = None
    ) -> int:
        """Create a new knowledge base.

        Args:
            name: Knowledge base name (must be unique)
            description: Knowledge base description
            avatar_url: Avatar URL

        Returns:
            Knowledge base ID

        Raises:
            Exception: If KB with same name already exists
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO knowledge_bases (name, description, avatar_url)
                VALUES (?, ?, ?)
            """, (name, description, avatar_url))

            conn.commit()
            kb_id = cursor.lastrowid

            logger.info(f"✅ Created knowledge base: {name} (ID: {kb_id})")
            return kb_id

        except sqlite3.IntegrityError as e:
            logger.error(f"❌ Knowledge base '{name}' already exists: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to create knowledge base: {e}")
            raise
        finally:
            conn.close()

    async def get_knowledge_base(self, kb_id: int) -> Optional[Dict[str, Any]]:
        """Get knowledge base by ID.

        Args:
            kb_id: Knowledge base ID

        Returns:
            Knowledge base info dict or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM knowledge_bases WHERE id = ?
            """, (kb_id,))

            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

        finally:
            conn.close()

    async def get_knowledge_base_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get knowledge base by name.

        Args:
            name: Knowledge base name

        Returns:
            Knowledge base info dict or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM knowledge_bases WHERE name = ?
            """, (name,))

            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

        finally:
            conn.close()

    async def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        """List all knowledge bases.

        Returns:
            List of knowledge base info dicts
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM knowledge_bases ORDER BY updated_at DESC
            """)

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

        finally:
            conn.close()

    async def update_knowledge_base(
        self,
        kb_id: int,
        name: str = None,
        description: str = None,
        avatar_url: str = None
    ) -> bool:
        """Update knowledge base information.

        Args:
            kb_id: Knowledge base ID
            name: New name (optional)
            description: New description (optional)
            avatar_url: New avatar URL (optional)

        Returns:
            True if successful, False otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            updates = []
            params = []

            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            if avatar_url is not None:
                updates.append("avatar_url = ?")
                params.append(avatar_url)

            if not updates:
                return True

            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(kb_id)

            query = f"UPDATE knowledge_bases SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()

            logger.info(f"✅ Updated knowledge base: ID {kb_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to update knowledge base: {e}")
            return False
        finally:
            conn.close()

    async def delete_knowledge_base(self, kb_id: int) -> bool:
        """Delete knowledge base (cascades to files).

        Args:
            kb_id: Knowledge base ID

        Returns:
            True if successful, False otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM knowledge_bases WHERE id = ?", (kb_id,))
            conn.commit()

            logger.info(f"✅ Deleted knowledge base: ID {kb_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to delete knowledge base: {e}")
            return False
        finally:
            conn.close()

    async def add_file(
        self,
        kb_id: int,
        filename: str,
        file_path: str,
        file_size: int,
        file_type: str
    ) -> int:
        """Add file to knowledge base (or update if exists).

        Args:
            kb_id: Knowledge base ID
            filename: Original filename
            file_path: Path in MinIO (e.g., "kb-name/filename")
            file_size: File size in bytes
            file_type: File type (md, txt, pdf)

        Returns:
            File ID

        Raises:
            Exception: If KB doesn't exist
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Check if file already exists
            cursor.execute("""
                SELECT id FROM kb_files WHERE kb_id = ? AND filename = ?
            """, (kb_id, filename))

            existing = cursor.fetchone()

            if existing:
                # Update existing file
                file_id = existing[0]
                cursor.execute("""
                    UPDATE kb_files
                    SET file_path = ?, file_size = ?, file_type = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (file_path, file_size, file_type, file_id))
                logger.info(f"✅ Updated file: {filename} (ID: {file_id})")
            else:
                # Insert new file
                cursor.execute("""
                    INSERT INTO kb_files (kb_id, filename, file_path, file_size, file_type)
                    VALUES (?, ?, ?, ?, ?)
                """, (kb_id, filename, file_path, file_size, file_type))
                file_id = cursor.lastrowid
                logger.info(f"✅ Added file: {filename} (ID: {file_id})")

            # Update KB stats
            cursor.execute("""
                UPDATE knowledge_bases
                SET doc_count = (SELECT COUNT(*) FROM kb_files WHERE kb_id = ?),
                    total_size = (SELECT SUM(file_size) FROM kb_files WHERE kb_id = ?),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (kb_id, kb_id, kb_id))

            conn.commit()
            return file_id

        except sqlite3.IntegrityError as e:
            logger.error(f"❌ KB doesn't exist: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to add file: {e}")
            raise
        finally:
            conn.close()

    async def get_kb_files(self, kb_id: int) -> List[Dict[str, Any]]:
        """Get all files in knowledge base.

        Args:
            kb_id: Knowledge base ID

        Returns:
            List of file info dicts
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM kb_files WHERE kb_id = ? ORDER BY uploaded_at DESC
            """, (kb_id,))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

        finally:
            conn.close()

    async def get_file(self, file_id: int) -> Optional[Dict[str, Any]]:
        """Get file by ID.

        Args:
            file_id: File ID

        Returns:
            File info dict or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM kb_files WHERE id = ?", (file_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

        finally:
            conn.close()

    async def delete_file(self, file_id: int) -> bool:
        """Delete file from knowledge base.

        Args:
            file_id: File ID

        Returns:
            True if successful, False otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Get KB ID before deleting
            cursor.execute("SELECT kb_id FROM kb_files WHERE id = ?", (file_id,))
            row = cursor.fetchone()
            if not row:
                return False

            kb_id = row[0]

            # Delete file
            cursor.execute("DELETE FROM kb_files WHERE id = ?", (file_id,))

            # Update KB stats
            cursor.execute("""
                UPDATE knowledge_bases
                SET doc_count = (SELECT COUNT(*) FROM kb_files WHERE kb_id = ?),
                    total_size = (SELECT SUM(file_size) FROM kb_files WHERE kb_id = ?),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (kb_id, kb_id, kb_id))

            conn.commit()
            logger.info(f"✅ Deleted file: ID {file_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to delete file: {e}")
            return False
        finally:
            conn.close()

    async def delete_kb_files(self, kb_id: int) -> int:
        """Delete all files in knowledge base.

        Args:
            kb_id: Knowledge base ID

        Returns:
            Number of files deleted
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT COUNT(*) FROM kb_files WHERE kb_id = ?", (kb_id,))
            count = cursor.fetchone()[0]

            cursor.execute("DELETE FROM kb_files WHERE kb_id = ?", (kb_id,))

            # Update KB stats
            cursor.execute("""
                UPDATE knowledge_bases
                SET doc_count = 0, total_size = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (kb_id,))

            conn.commit()
            logger.info(f"✅ Deleted {count} files from KB: ID {kb_id}")
            return count

        except Exception as e:
            logger.error(f"❌ Failed to delete KB files: {e}")
            return 0
        finally:
            conn.close()
