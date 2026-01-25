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
        # 模型配置表
        self.execute("""
            CREATE TABLE IF NOT EXISTS model_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                model_path TEXT NOT NULL,
                is_current BOOLEAN DEFAULT 0,
                is_downloaded BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

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

    # Model configuration methods
    def add_model(self, model_name: str, model_path: str) -> int:
        """
        Add a new model to the configuration
        自动检查文件是否存在，设置 is_downloaded 状态
        """
        from pathlib import Path

        # 检查文件是否存在
        is_downloaded = Path(model_path).exists()

        cursor = self.execute(
            "INSERT INTO model_config (model_name, model_path, is_downloaded) VALUES (?, ?, ?)",
            (model_name, model_path, is_downloaded)
        )
        return cursor.lastrowid

    def get_model(self, model_id: int) -> Optional[Dict[str, Any]]:
        """Get model by ID"""
        return self.fetchone(
            "SELECT * FROM model_config WHERE id = ?",
            (model_id,)
        )

    def get_model_by_name(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get model by name"""
        return self.fetchone(
            "SELECT * FROM model_config WHERE model_name = ?",
            (model_name,)
        )

    def get_all_models(self) -> List[Dict[str, Any]]:
        """获取所有可用模型"""
        query = """
            SELECT
                id,
                model_name,
                model_path,
                is_current,
                is_downloaded,
                created_at,
                updated_at
            FROM model_config
            ORDER BY created_at DESC
        """
        return self.fetchall(query)

    def get_current_model(self) -> Optional[Dict[str, Any]]:
        """获取当前活动模型"""
        query = """
            SELECT
                id,
                model_name,
                model_path,
                is_current,
                is_downloaded,
                created_at,
                updated_at
            FROM model_config
            WHERE is_current = 1
        """
        return self.fetchone(query)

    def set_current_model(self, model_id: int) -> bool:
        """Set a model as the current active model"""
        # First, unset all current models
        self.execute("UPDATE model_config SET is_current = 0")
        # Then set the specified model as current
        self.execute(
            "UPDATE model_config SET is_current = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
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
            "UPDATE model_config SET is_downloaded = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
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
        self.execute("DELETE FROM model_config WHERE id = ?", (model_id,))
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
