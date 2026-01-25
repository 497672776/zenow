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
        llm_server: LLMServer,
        db_config: SQLiteConfig
    ):
        self.models_dir = models_dir
        self.downloader = downloader
        self.llm_server = llm_server
        self.db_config = db_config
        self.models_dir.mkdir(parents=True, exist_ok=True)

    async def select_model(
        self,
        model_name: str,
        download_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute complete model selection flow"""
        logger.info(f"Starting model selection: {model_name}")

        try:
            # Step 1: Check if model exists
            model_path = await self._check_model_exists(model_name)

            # Step 2: Download if not exists and URL provided
            if not model_path and download_url:
                logger.info(f"Model not found, downloading: {download_url}")
                model_path = await self._download_model(download_url, model_name)
                if not model_path:
                    return {
                        "success": False,
                        "message": "Model download failed",
                        "model_name": model_name,
                        "model_path": None,
                        "server_status": "error"
                    }

            # Step 2.5: Return error if still no model path
            if not model_path:
                return {
                    "success": False,
                    "message": f"Model {model_name} not found and no download URL provided",
                    "model_name": model_name,
                    "model_path": None,
                    "server_status": "error"
                }

            # Step 3: Ensure llama-server is running
            server_ready = await self._ensure_server_running(model_name, model_path)
            if not server_ready:
                return {
                    "success": False,
                    "message": "Failed to start llama-server",
                    "model_name": model_name,
                    "model_path": str(model_path),
                    "server_status": "error"
                }

            # Step 4: Update database
            await self._update_database(model_name, str(model_path))

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

    async def _check_model_exists(self, model_name: str) -> Optional[Path]:
        """Check if model file exists"""
        possible_names = [
            f"{model_name}.gguf",
            f"{model_name}.GGUF",
        ]

        for filename in possible_names:
            model_path = self.models_dir / filename
            if model_path.exists():
                logger.info(f"Found model file: {model_path}")
                return model_path

        logger.info(f"Model not found: {model_name}")
        return None

    async def _download_model(
        self,
        url: str,
        expected_name: str
    ) -> Optional[Path]:
        """Download model file"""
        try:
            await self.downloader.start_download(url)

            # Poll download status until complete
            max_wait_time = 30 * 60  # 30 minutes timeout
            check_interval = 1
            elapsed = 0

            while elapsed < max_wait_time:
                status = self.downloader.get_download_status(url)

                if status and status["status"] == "completed":
                    logger.info(f"Download completed: {status['filename']}")
                    return Path(status["filename"])

                if status and status["status"] == "failed":
                    logger.error(f"Download failed: {status.get('error')}")
                    return None

                await asyncio.sleep(check_interval)
                elapsed += check_interval

            logger.error(f"Download timeout: {url}")
            return None

        except Exception as e:
            logger.error(f"Error downloading model: {e}", exc_info=True)
            return None

    async def _ensure_server_running(
        self,
        model_name: str,
        model_path: Path
    ) -> bool:
        """
        Ensure llama-server is running with specified model.

        Rules:
        1. If same model is already running -> do nothing
        2. If different model is running -> kill old process and start new one
        3. If no model is running -> start new one

        This ensures:
        - Only one model process runs at a time
        - Same model won't start multiple times
        - Switching models always kills the old process first
        """
        try:
            current_status = self.llm_server.get_status()
            current_model_path = current_status.get("model_path")
            is_running = current_status.get("is_running")

            # Normalize paths for comparison
            target_path_str = str(model_path.resolve())
            current_path_str = str(Path(current_model_path).resolve()) if current_model_path else None

            logger.info(f"Target model path: {target_path_str}")
            logger.info(f"Current model path: {current_path_str}")
            logger.info(f"Server is_running: {is_running}")

            # Case 1: Same model already running -> do nothing
            if is_running and current_path_str == target_path_str:
                logger.info(f"✓ llama-server already running with target model: {model_name}")
                logger.info(f"  Skipping restart to avoid duplicate processes")
                return True

            # Case 2: Different model running OR server stopped
            if is_running:
                logger.info(f"✗ Different model detected!")
                logger.info(f"  Current: {current_model_path}")
                logger.info(f"  Target:  {target_path_str}")
                logger.info(f"  Stopping old llama-server process...")

                # Kill the old process
                stop_success = await self.llm_server.stop()
                if not stop_success:
                    logger.error("Failed to stop old llama-server")
                    return False

                # Wait for process to fully terminate
                await asyncio.sleep(3)
                logger.info("  Old process stopped successfully")

            # Case 3: Start new server (either no server was running, or we just stopped it)
            logger.info(f"→ Starting llama-server with model: {model_name}")
            logger.info(f"  Model path: {target_path_str}")

            success = await self.llm_server.start(str(model_path), model_name)

            if not success:
                logger.error("✗ Failed to start llama-server")
                return False

            # Wait for server to be ready
            logger.info("  Waiting for server to be ready...")
            max_wait = 30
            for i in range(max_wait):
                status = self.llm_server.get_status()
                if status.get("is_running") and status.get("status") == "running":
                    logger.info(f"✓ llama-server started successfully after {i+1}s")
                    return True
                await asyncio.sleep(1)

            logger.error(f"✗ llama-server startup timeout (waited {max_wait}s)")
            return False

        except Exception as e:
            logger.error(f"✗ Error managing llama-server: {e}", exc_info=True)
            return False

    async def _update_database(self, model_name: str, model_path: str) -> None:
        """Update model info in database"""
        try:
            existing_model = self.db_config.get_model_by_name(model_name)

            if existing_model:
                model_id = existing_model["id"]
                logger.info(f"Model exists in DB: {model_name} (ID: {model_id})")
            else:
                model_id = self.db_config.add_model(model_name, model_path)
                logger.info(f"Added model to DB: {model_name} (ID: {model_id})")

            self.db_config.set_current_model(model_id)
            logger.info(f"Set current model: {model_name}")

        except Exception as e:
            logger.error(f"Error updating database: {e}", exc_info=True)
            raise
