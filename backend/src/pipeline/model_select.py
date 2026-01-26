"""
Model Selection Pipeline
"""

import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

from ..model.download import ModelDownloader
from ..model.llm import LLMServer
from ..comon.sqlite.sqlite_config import SQLiteConfig

logger = logging.getLogger(__name__)


class ModelSelectionPipeline:
    """Model selection pipeline manager"""

    def __init__(
        self,
        models_dir: Path,
        downloader: ModelDownloader,
        server_manager,  # ModelServerManager instance
        db_config: SQLiteConfig
    ):
        self.models_dir = models_dir
        self.downloader = downloader
        self.server_manager = server_manager
        self.db_config = db_config
        self.models_dir.mkdir(parents=True, exist_ok=True)

    async def select_model(
        self,
        model_name: str,
        download_url: Optional[str] = None,
        mode: str = "llm"
    ) -> Dict[str, Any]:
        """
        Execute complete model selection flow

        Args:
            model_name: Name of the model
            download_url: Optional URL to download the model (if not provided, will try to get from database)
            mode: Model mode ('llm', 'embed', 'rerank')
        """
        logger.info(f"Starting model selection: {model_name} (mode: {mode})")

        try:
            # Step 1: Check if model exists
            model_path = await self._check_model_exists(model_name, mode)

            # Step 2: If model not found, try to get download URL from database
            if not model_path and not download_url:
                existing_model = self.db_config.get_model_by_name(model_name, mode)
                if existing_model and existing_model.get('download_url'):
                    download_url = existing_model['download_url']
                    logger.info(f"Found download URL in database: {download_url}")

            # Step 3: Download if not exists and URL available
            if not model_path and download_url:
                logger.info(f"Model not found, downloading: {download_url}")
                model_path = await self._download_model(download_url, model_name, mode)
                if not model_path:
                    return {
                        "success": False,
                        "message": "Model download failed",
                        "model_name": model_name,
                        "model_path": None,
                        "server_status": "error"
                    }

            # Step 4: Return error if still no model path
            if not model_path:
                return {
                    "success": False,
                    "message": f"Model {model_name} not found and no download URL available",
                    "model_name": model_name,
                    "model_path": None,
                    "server_status": "error"
                }

            # Step 5: Ensure llama-server is running
            server_ready = await self._ensure_server_running(model_name, model_path, mode)
            if not server_ready:
                return {
                    "success": False,
                    "message": "Failed to start llama-server",
                    "model_name": model_name,
                    "model_path": str(model_path),
                    "server_status": "error"
                }

            # Step 6: Update database
            await self._update_database(model_name, str(model_path), mode)

            logger.info(f"Model selection completed: {model_name}")
            return {
                "success": True,
                "message": f"Successfully switched to model: {model_name}",
                "model_name": model_name,
                "model_path": str(model_path),
                "server_status": "running"
            }

        except Exception as e:
            logger.error(f"Model selection failed: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Model selection error: {str(e)}",
                "model_name": model_name,
                "model_path": None,
                "server_status": "error"
            }

    async def _check_model_exists(self, model_name: str, mode: str = "llm") -> Optional[Path]:
        """
        Check if model file exists
        First checks database for existing model path, then checks default directory

        Args:
            model_name: Name of the model
            mode: Model mode ('llm', 'embed', 'rerank')
        """
        from ..config import get_model_dir

        # First, check if model exists in database
        existing_model = self.db_config.get_model_by_name(model_name, mode)
        if existing_model:
            model_path = Path(existing_model['model_path'])
            if model_path.exists():
                logger.info(f"Found model in database: {model_path}")
                return model_path
            else:
                logger.info(f"Model in database but file not found: {model_path}")

        # If not in database or file doesn't exist, check default directory
        mode_dir = get_model_dir(mode)

        possible_names = [
            f"{model_name}.gguf",
            f"{model_name}.GGUF",
        ]

        for filename in possible_names:
            model_path = mode_dir / filename
            if model_path.exists():
                logger.info(f"Found model file in directory: {model_path}")
                return model_path

        logger.info(f"Model not found: {model_name} (mode: {mode})")
        return None

    async def _download_model(
        self,
        url: str,
        expected_name: str,
        mode: str = "llm"
    ) -> Optional[Path]:
        """
        Download model file

        Args:
            url: Download URL
            expected_name: Expected model name
            mode: Model mode ('llm', 'embed', 'rerank')
        """
        try:
            from ..config import get_model_dir

            # Get the correct directory for this mode
            mode_dir = get_model_dir(mode)

            # Update downloader's download directory
            original_download_dir = self.downloader.download_dir
            self.downloader.download_dir = mode_dir

            # download_model() is async and returns the path when complete
            model_path = await self.downloader.download_model(url)
            logger.info(f"Download completed: {model_path}")

            # Restore original download directory
            self.downloader.download_dir = original_download_dir

            return model_path

        except Exception as e:
            logger.error(f"Error downloading model: {e}", exc_info=True)
            return None

    async def _ensure_server_running(
        self,
        model_name: str,
        model_path: Path,
        mode: str = "llm"
    ) -> bool:
        """
        Ensure llama-server is running with specified model.

        Rules:
        1. If same model is already running -> do nothing
        2. If different model is running -> kill old process and start new one
        3. If no model is running -> start new one

        This ensures:
        - Only one model process runs at a time per mode
        - Same model won't start multiple times
        - Switching models always kills the old process first

        Args:
            model_name: Name of the model
            model_path: Path to the model file
            mode: Model mode ('llm', 'embed', 'rerank')
        """
        try:
            # Get the server for this mode
            llm_server = self.server_manager.get_server(mode)

            current_status = llm_server.get_status()
            current_model_path = current_status.get("model_path")
            is_running = current_status.get("is_running")

            # Normalize paths for comparison
            target_path_str = str(model_path.resolve())
            current_path_str = str(Path(current_model_path).resolve()) if current_model_path else None

            logger.info(f"[{mode.upper()}] Target model path: {target_path_str}")
            logger.info(f"[{mode.upper()}] Current model path: {current_path_str}")
            logger.info(f"[{mode.upper()}] Server is_running: {is_running}")

            # Case 1: Same model already running -> do nothing
            if is_running and current_path_str == target_path_str:
                logger.info(f"✓ [{mode.upper()}] llama-server already running with target model: {model_name}")
                logger.info(f"  Skipping restart to avoid duplicate processes")
                return True

            # Case 2: Different model running OR server stopped
            if is_running:
                logger.info(f"✗ [{mode.upper()}] Different model detected!")
                logger.info(f"  Current: {current_model_path}")
                logger.info(f"  Target:  {target_path_str}")
                logger.info(f"  Stopping old llama-server process...")

                # Kill the old process
                stop_success = await llm_server.stop()
                if not stop_success:
                    logger.error(f"[{mode.upper()}] Failed to stop old llama-server")
                    return False

                # Wait for process to fully terminate
                await asyncio.sleep(3)
                logger.info(f"  [{mode.upper()}] Old process stopped successfully")

            # Case 3: Start new server (either no server was running, or we just stopped it)
            logger.info(f"→ [{mode.upper()}] Starting llama-server with model: {model_name}")
            logger.info(f"  Model path: {target_path_str}")

            success = await llm_server.start(str(model_path), model_name)

            if not success:
                logger.error(f"✗ [{mode.upper()}] Failed to start llama-server")
                return False

            # Wait for server to be ready
            logger.info(f"  [{mode.upper()}] Waiting for server to be ready...")
            max_wait = 30
            for i in range(max_wait):
                status = llm_server.get_status()
                if status.get("is_running") and status.get("status") == "running":
                    logger.info(f"✓ [{mode.upper()}] llama-server started successfully after {i+1}s")
                    return True
                await asyncio.sleep(1)

            logger.error(f"✗ [{mode.upper()}] llama-server startup timeout (waited {max_wait}s)")
            return False

        except Exception as e:
            logger.error(f"✗ [{mode.upper()}] Error managing llama-server: {e}", exc_info=True)
            return False

    async def _update_database(self, model_name: str, model_path: str, mode: str = "llm") -> None:
        """
        Update model info in database

        Args:
            model_name: Name of the model
            model_path: Path to the model file
            mode: Model mode ('llm', 'embed', 'rerank')
        """
        try:
            from pathlib import Path

            existing_model = self.db_config.get_model_by_name(model_name, mode)

            if existing_model:
                model_id = existing_model["id"]
                logger.info(f"Model exists in DB: {model_name} (ID: {model_id}, mode: {mode})")

                # 检查文件是否存在并更新 is_downloaded 状态
                is_downloaded = Path(model_path).exists()
                self.db_config.update_model_download_status(model_id, is_downloaded)
                logger.info(f"Updated download status: is_downloaded={is_downloaded}")
            else:
                model_id = self.db_config.add_model(model_name, model_path, mode)
                logger.info(f"Added model to DB: {model_name} (ID: {model_id}, mode: {mode})")

            # Set as current model (will validate that it's downloaded)
            try:
                self.db_config.set_current_model(model_id, mode)
                logger.info(f"Set current model: {model_name} (mode: {mode})")
            except ValueError as e:
                logger.error(f"Cannot set model as current: {e}")
                raise

        except Exception as e:
            logger.error(f"Error updating database: {e}", exc_info=True)
            raise
