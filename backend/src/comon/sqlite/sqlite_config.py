"""
SQLite configuration management for Zenow backend
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from .sqlite_base import SQLiteBase
from ...config import DATABASE_PATH


class SQLiteConfig(SQLiteBase):
    """SQLite database class for configuration persistence"""

    def __init__(self, db_path: Path = DATABASE_PATH):
        """Initialize configuration database"""
        super().__init__(db_path)

    def _init_db(self):
        """Initialize configuration tables"""
        # Model configuration table
        self.execute("""
            CREATE TABLE IF NOT EXISTS model_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                model_path TEXT NOT NULL,
                is_current BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # LLM parameters table
        self.execute("""
            CREATE TABLE IF NOT EXISTS llm_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parameter_name TEXT NOT NULL UNIQUE,
                parameter_value TEXT NOT NULL,
                parameter_type TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Model status table
        self.execute("""
            CREATE TABLE IF NOT EXISTS model_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    # Model configuration methods
    def add_model(self, model_name: str, model_path: str) -> int:
        """Add a new model to the configuration"""
        cursor = self.execute(
            "INSERT INTO model_config (model_name, model_path) VALUES (?, ?)",
            (model_name, model_path)
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
        """Get all available models with their status"""
        query = """
            SELECT
                mc.id,
                mc.model_name,
                mc.model_path,
                mc.is_current,
                mc.created_at,
                mc.updated_at,
                COALESCE(ms.status, 'not_started') as status,
                ms.error_message
            FROM model_config mc
            LEFT JOIN model_status ms ON mc.model_name = ms.model_name
            ORDER BY mc.created_at DESC
        """
        return self.fetchall(query)

    def get_current_model(self) -> Optional[Dict[str, Any]]:
        """Get the current active model with its status"""
        query = """
            SELECT
                mc.id,
                mc.model_name,
                mc.model_path,
                mc.is_current,
                mc.created_at,
                mc.updated_at,
                COALESCE(ms.status, 'not_started') as status,
                ms.error_message
            FROM model_config mc
            LEFT JOIN model_status ms ON mc.model_name = ms.model_name
            WHERE mc.is_current = 1
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

    # Model status methods
    def update_model_status(self, model_name: str, status: str, error_message: Optional[str] = None) -> None:
        """Update model status"""
        # Delete old status for this model
        self.execute("DELETE FROM model_status WHERE model_name = ?", (model_name,))
        # Insert new status
        self.execute(
            "INSERT INTO model_status (model_name, status, error_message) VALUES (?, ?, ?)",
            (model_name, status, error_message)
        )

    def get_model_status(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get model status"""
        return self.fetchone(
            "SELECT * FROM model_status WHERE model_name = ? ORDER BY updated_at DESC LIMIT 1",
            (model_name,)
        )
