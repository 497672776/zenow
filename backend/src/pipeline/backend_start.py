"""
Backend startup handler
Automatically loads and starts the current model when backend starts
If config.db doesn't exist, creates it using config.py defaults
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class BackendStartupHandler:
    """Handle model loading on backend startup"""

    def __init__(self, llm_server, db_config, config):
        """
        Initialize startup handler

        Args:
            llm_server: LLMServer instance
            db_config: SQLiteConfig instance
            config: Config module
        """
        self.llm_server = llm_server
        self.db_config = db_config
        self.config = config

    async def initialize(self):
        """
        Initialize backend on startup:
        1. Check if config.db exists and has data
        2. If not, create it using config.py defaults
        3. Get current model from config.db
        4. Start llama-server with the model
        """
        logger.info("=" * 80)
        logger.info("BACKEND STARTUP - Initializing model")
        logger.info("=" * 80)

        try:
            # Step 1: Ensure database is initialized
            self._ensure_database_initialized()

            # Step 2: Get current model from database
            model_to_load = self._get_model_from_db()

            # Step 3: If we have a model, start it
            if model_to_load:
                await self._start_model(model_to_load)
            else:
                logger.warning("⚠ No model configured, llama-server will not start")
                logger.info("  Please download and select a model via the UI")

        except Exception as e:
            logger.error(f"Error during backend startup: {e}", exc_info=True)

        logger.info("=" * 80)

    def _ensure_database_initialized(self):
        """
        Ensure config.db exists and has default configuration
        If database doesn't exist or is empty, create it using config.py
        """
        try:
            # Try to get all models
            models = self.db_config.get_all_models()

            if models and len(models) > 0:
                logger.info(f"✓ Database exists with {len(models)} model(s)")
                return

            # Database is empty, initialize with defaults
            logger.info("Database is empty, initializing with config.py defaults...")
            self._create_database_from_config()

        except Exception as e:
            logger.warning(f"Database error: {e}")
            logger.info("Creating new database from config.py...")
            self._create_database_from_config()

    def _create_database_from_config(self):
        """
        Create config.db using default configuration from config.py
        """
        logger.info("Creating config.db from config.py defaults...")

        # Check if default model URLs are configured
        if not hasattr(self.config, 'DEFAULT_MODEL_DOWNLOAD_URLS'):
            logger.warning("⚠ No DEFAULT_MODEL_DOWNLOAD_URLS in config.py")
            logger.info("  Database will be created but empty")
            return

        if not self.config.DEFAULT_MODEL_DOWNLOAD_URLS:
            logger.warning("⚠ DEFAULT_MODEL_DOWNLOAD_URLS is empty")
            logger.info("  Database will be created but empty")
            return

        # Get first default model URL
        default_url = self.config.DEFAULT_MODEL_DOWNLOAD_URLS[0]
        filename = default_url.split('/')[-1]
        model_name = filename.replace('.gguf', '').replace('.GGUF', '')
        model_path = self.config.MODELS_DIR / filename

        logger.info(f"Default model from config.py:")
        logger.info(f"  Name: {model_name}")
        logger.info(f"  URL: {default_url}")
        logger.info(f"  Path: {model_path}")

        # Check if model file exists
        if not model_path.exists():
            logger.warning(f"⚠ Model file not found at: {model_path}")
            logger.info("  The model will need to be downloaded via the UI")

        try:
            # Add model to database
            model_id = self.db_config.add_model(model_name, str(model_path))
            logger.info(f"✓ Added model to database (ID: {model_id})")

            # Set as current model
            self.db_config.set_current_model(model_id)
            logger.info(f"✓ Set as current model")
            logger.info("✓ config.db created successfully")

        except Exception as e:
            logger.error(f"✗ Failed to create database: {e}", exc_info=True)

    def _get_model_from_db(self):
        """
        Get current model from config.db

        Returns:
            dict with model info or None
        """
        try:
            current_model = self.db_config.get_current_model()

            if not current_model:
                logger.info("ℹ No current model set in database")
                return None

            model_path = Path(current_model["model_path"])

            # Verify model file exists
            if model_path.exists():
                logger.info(f"✓ Current model:")
                logger.info(f"  Name: {current_model['model_name']}")
                logger.info(f"  Path: {current_model['model_path']}")
                return current_model
            else:
                logger.warning(f"⚠ Current model file not found:")
                logger.warning(f"  Path: {current_model['model_path']}")
                logger.info("  Please download the model via the UI")
                return None

        except Exception as e:
            logger.error(f"Error getting model from database: {e}", exc_info=True)
            return None

    async def _start_model(self, model_info):
        """
        Start llama-server with the given model

        Args:
            model_info: dict with 'model_name' and 'model_path'
        """
        model_name = model_info["model_name"]
        model_path = model_info["model_path"]

        logger.info(f"→ Starting llama-server with model: {model_name}")
        logger.info(f"  Path: {model_path}")

        try:
            # Use async wrapper
            success = await self.llm_server.start(model_path, model_name)

            if success:
                logger.info("✓ llama-server started successfully")
            else:
                logger.error("✗ Failed to start llama-server")
                logger.error("  Check logs above for details")

        except Exception as e:
            logger.error(f"✗ Error starting llama-server: {e}", exc_info=True)
