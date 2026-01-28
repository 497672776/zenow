"""
SQLite configuration management for Zenow backend
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from .sqlite_base import SQLiteBase


class SQLiteConfig(SQLiteBase):
    """SQLite database class for configuration persistence"""

    def __init__(self, db_path: Path):
        """Initialize configuration database"""
        super().__init__(db_path)

    def _init_db(self):
        """初始化配置表"""
        # 检查是否需要迁移旧表
        self._migrate_model_config_to_model_info()

        # 模型信息表（支持多模式：llm, embed, rerank）
        self.execute("""
            CREATE TABLE IF NOT EXISTS model_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                model_path TEXT NOT NULL,
                download_url TEXT,
                mode TEXT NOT NULL DEFAULT 'llm',
                is_current BOOLEAN DEFAULT 0,
                is_downloaded BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(model_name, mode)
            )
        """)

        # 为已存在的表添加 download_url 字段（如果不存在）
        self._add_download_url_column_if_not_exists()

        # LLM 参数表
        self.execute("""
            CREATE TABLE IF NOT EXISTS llm_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parameter_name TEXT NOT NULL UNIQUE,
                parameter_value TEXT NOT NULL,
                parameter_type TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def _migrate_model_config_to_model_info(self):
        """从旧的 model_config 表迁移数据到新的 model_info 表"""
        # 检查旧表是否存在
        result = self.fetchone("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='model_config'
        """)

        if result:
            # 创建新表（如果不存在）
            self.execute("""
                CREATE TABLE IF NOT EXISTS model_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    model_path TEXT NOT NULL,
                    mode TEXT NOT NULL DEFAULT 'llm',
                    is_current BOOLEAN DEFAULT 0,
                    is_downloaded BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(model_name, mode)
                )
            """)

            # 迁移数据（默认 mode='llm'）
            self.execute("""
                INSERT OR IGNORE INTO model_info
                    (model_name, model_path, mode, is_current, is_downloaded, created_at, updated_at)
                SELECT
                    model_name, model_path, 'llm', is_current, is_downloaded, created_at, updated_at
                FROM model_config
            """)

            # 删除旧表
            self.execute("DROP TABLE model_config")

    def _add_download_url_column_if_not_exists(self):
        """为已存在的 model_info 表添加 download_url 字段"""
        try:
            # 检查 download_url 列是否存在
            result = self.fetchone("""
                SELECT COUNT(*) as count
                FROM pragma_table_info('model_info')
                WHERE name='download_url'
            """)

            if result and result['count'] == 0:
                # 添加 download_url 列
                self.execute("ALTER TABLE model_info ADD COLUMN download_url TEXT")
        except Exception as e:
            # 如果出错，可能是表不存在或其他问题，忽略
            pass

    # Model configuration methods
    def add_model(self, model_name: str, model_path: str, mode: str = "llm", download_url: str = None) -> int:
        """
        Add a new model to the configuration
        自动检查文件是否存在，设置 is_downloaded 状态

        Args:
            model_name: 模型名称
            model_path: 模型路径
            mode: 模型模式 ('llm', 'embed', 'rerank')
            download_url: 模型下载地址（可选）
        """
        from pathlib import Path

        # 检查文件是否存在
        is_downloaded = Path(model_path).exists()

        cursor = self.execute(
            "INSERT INTO model_info (model_name, model_path, download_url, mode, is_downloaded) VALUES (?, ?, ?, ?, ?)",
            (model_name, model_path, download_url, mode, is_downloaded)
        )
        return cursor.lastrowid

    def get_model(self, model_id: int) -> Optional[Dict[str, Any]]:
        """Get model by ID"""
        return self.fetchone(
            "SELECT * FROM model_info WHERE id = ?",
            (model_id,)
        )

    def get_model_by_name(self, model_name: str, mode: str = "llm") -> Optional[Dict[str, Any]]:
        """Get model by name and mode"""
        return self.fetchone(
            "SELECT * FROM model_info WHERE model_name = ? AND mode = ?",
            (model_name, mode)
        )

    def get_all_models(self, mode: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取所有可用模型

        Args:
            mode: 可选，筛选特定模式的模型 ('llm', 'embed', 'rerank')
        """
        if mode:
            query = """
                SELECT
                    id,
                    model_name,
                    model_path,
                    download_url,
                    mode,
                    is_current,
                    is_downloaded,
                    created_at,
                    updated_at
                FROM model_info
                WHERE mode = ?
                ORDER BY created_at DESC
            """
            return self.fetchall(query, (mode,))
        else:
            query = """
                SELECT
                    id,
                    model_name,
                    model_path,
                    download_url,
                    mode,
                    is_current,
                    is_downloaded,
                    created_at,
                    updated_at
                FROM model_info
                ORDER BY created_at DESC
            """
            return self.fetchall(query)

    def get_current_model(self, mode: str = "llm") -> Optional[Dict[str, Any]]:
        """
        获取当前活动模型

        Args:
            mode: 模型模式 ('llm', 'embed', 'rerank')
        """
        query = """
            SELECT
                id,
                model_name,
                model_path,
                download_url,
                mode,
                is_current,
                is_downloaded,
                created_at,
                updated_at
            FROM model_info
            WHERE is_current = 1 AND mode = ?
        """
        return self.fetchone(query, (mode,))

    def set_current_model(self, model_id: int, mode: str = "llm") -> bool:
        """
        Set a model as the current active model
        Only allows setting downloaded models as current

        Args:
            model_id: 模型 ID
            mode: 模型模式 ('llm', 'embed', 'rerank')

        Returns:
            True if successful, False if model is not downloaded

        Raises:
            ValueError: If model doesn't exist or is not downloaded
        """
        # Check if model exists and is downloaded
        model = self.get_model(model_id)
        if not model:
            raise ValueError(f"Model with ID {model_id} does not exist")

        if not model.get('is_downloaded', False):
            raise ValueError(
                f"Cannot set model '{model['model_name']}' as current: "
                f"model file not downloaded at {model['model_path']}"
            )

        # Verify mode matches
        if model.get('mode') != mode:
            raise ValueError(
                f"Model mode mismatch: expected '{mode}', got '{model.get('mode')}'"
            )

        # First, unset all current models for this mode
        self.execute("UPDATE model_info SET is_current = 0 WHERE mode = ?", (mode,))
        # Then set the specified model as current
        self.execute(
            "UPDATE model_info SET is_current = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (model_id,)
        )
        return True

    def update_model_download_status(self, model_id: int, is_downloaded: bool) -> bool:
        """
        更新模型的下载状态

        Args:
            model_id: 模型 ID
            is_downloaded: 是否已下载

        Returns:
            更新是否成功
        """
        self.execute(
            "UPDATE model_info SET is_downloaded = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (is_downloaded, model_id)
        )
        return True

    def check_and_update_download_status(self, model_id: int) -> bool:
        """
        检查文件是否存在并更新下载状态

        Args:
            model_id: 模型 ID

        Returns:
            文件是否存在
        """
        from pathlib import Path

        model = self.get_model(model_id)
        if not model:
            return False

        model_path = Path(model['model_path'])
        is_downloaded = model_path.exists()

        self.update_model_download_status(model_id, is_downloaded)
        return is_downloaded

    def delete_model(self, model_id: int) -> bool:
        """Delete a model from configuration"""
        self.execute("DELETE FROM model_info WHERE id = ?", (model_id,))
        return True

    # LLM parameters methods
    def set_parameter(self, name: str, value: Any, param_type: str = "string") -> None:
        """Set a parameter value"""
        value_str = json.dumps(value) if param_type in ["dict", "list"] else str(value)
        self.execute("""
            INSERT INTO llm_parameters (parameter_name, parameter_value, parameter_type)
            VALUES (?, ?, ?)
            ON CONFLICT(parameter_name) DO UPDATE SET
                parameter_value = excluded.parameter_value,
                parameter_type = excluded.parameter_type,
                updated_at = CURRENT_TIMESTAMP
        """, (name, value_str, param_type))

    def get_parameter(self, name: str, default: Any = None) -> Any:
        """Get a parameter value"""
        result = self.fetchone(
            "SELECT parameter_value, parameter_type FROM llm_parameters WHERE parameter_name = ?",
            (name,)
        )
        if not result:
            return default

        value_str = result['parameter_value']
        param_type = result['parameter_type']

        # Convert based on type
        if param_type == "int":
            return int(value_str)
        elif param_type == "float":
            return float(value_str)
        elif param_type == "bool":
            return value_str.lower() == "true"
        elif param_type in ["dict", "list"]:
            return json.loads(value_str)
        else:
            return value_str

    def get_all_parameters(self) -> Dict[str, Any]:
        """Get all parameters"""
        results = self.fetchall("SELECT parameter_name, parameter_value, parameter_type FROM llm_parameters")
        params = {}
        for row in results:
            name = row['parameter_name']
            value_str = row['parameter_value']
            param_type = row['parameter_type']

            if param_type == "int":
                params[name] = int(value_str)
            elif param_type == "float":
                params[name] = float(value_str)
            elif param_type == "bool":
                params[name] = value_str.lower() == "true"
            elif param_type in ["dict", "list"]:
                params[name] = json.loads(value_str)
            else:
                params[name] = value_str

        return params
