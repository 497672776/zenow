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

    def __init__(self, server_manager, db_config, config):
        """
        Initialize startup handler

        Args:
            server_manager: ModelServerManager instance
            db_config: SQLiteConfig instance
            config: Config module
        """
        self.server_manager = server_manager
        self.db_config = db_config
        self.config = config

    async def initialize(self):
        """
        Initialize backend on startup:
        1. Check if config.db exists and has data
        2. If not, create it using config.py defaults
        3. Load parameters from database (if exists)
        4. Get current models for all modes from config.db
        5. Start llama-server for each current model
        """
        logger.info("=" * 80)
        logger.info("BACKEND STARTUP - Initializing")
        logger.info("=" * 80)

        try:
            # Step 1: Ensure database is initialized
            self._ensure_database_initialized()

            # Step 2: Load parameters from database
            self._load_parameters_from_db()

            # Step 3: Start all current models (LLM, Embed, Rerank)
            await self._start_all_current_models()

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

        # Add all default models from config.py (now organized by mode)
        total_added = 0
        first_llm_model_id = None

        for mode, urls in self.config.DEFAULT_MODEL_DOWNLOAD_URLS.items():
            logger.info(f"Adding {len(urls)} default {mode.upper()} models from config.py:")

            for idx, default_url in enumerate(urls, 1):
                try:
                    filename = default_url.split('/')[-1]
                    model_name = filename.replace('.gguf', '').replace('.GGUF', '')

                    # Get the correct directory for this mode
                    from config import get_model_dir
                    model_dir = get_model_dir(mode)
                    model_path = model_dir / filename

                    logger.info(f"  [{idx}] {model_name} (mode: {mode})")
                    logger.info(f"      URL: {default_url}")
                    logger.info(f"      Path: {model_path}")

                    # Check if model file exists
                    if not model_path.exists():
                        logger.warning(f"      ⚠ File not found (will need download)")
                    else:
                        logger.info(f"      ✓ File exists")

                    # Add model to database with mode and download_url
                    model_id = self.db_config.add_model(
                        model_name,
                        str(model_path),
                        mode,
                        download_url=default_url
                    )
                    logger.info(f"      ✓ Added to database (ID: {model_id})")

                    # Remember first LLM model ID to set as current
                    if mode == "llm" and first_llm_model_id is None:
                        first_llm_model_id = model_id

                    total_added += 1

                except Exception as e:
                    logger.error(f"      ✗ Failed to add model: {e}")
                    continue

        # Set first LLM model as current (only if downloaded)
        if first_llm_model_id is not None:
            try:
                # Check if the model is downloaded before setting as current
                model = self.db_config.get_model(first_llm_model_id)
                if model and model.get('is_downloaded', False):
                    self.db_config.set_current_model(first_llm_model_id, "llm")
                    logger.info(f"✓ Set first LLM model as current (ID: {first_llm_model_id})")
                else:
                    logger.warning(f"⚠ First LLM model not downloaded, skipping set as current (ID: {first_llm_model_id})")
            except ValueError as e:
                logger.warning(f"⚠ Cannot set model as current: {e}")
            except Exception as e:
                logger.error(f"✗ Failed to set current model: {e}")

        if total_added > 0:
            logger.info(f"✓ config.db created successfully with {total_added} models")
        else:
            logger.warning("⚠ config.db created but no models were added")

        # Initialize default LLM parameters
        self._initialize_default_parameters()

    def _initialize_default_parameters(self):
        """
        初始化默认的 LLM 参数到数据库
        只在数据库为空时执行
        """
        try:
            # 检查是否已有参数
            existing_params = self.db_config.get_all_parameters()
            if existing_params:
                logger.info("ℹ 参数已存在，跳过初始化")
                return

            logger.info("→ 初始化默认参数到数据库...")

            # Server 参数
            self.db_config.set_parameter("context_size", self.config.LLM_SERVER_CONTEXT_SIZE, "int")
            self.db_config.set_parameter("threads", self.config.LLM_SERVER_THREADS, "int")
            self.db_config.set_parameter("gpu_layers", self.config.LLM_SERVER_GPU_LAYERS, "int")
            self.db_config.set_parameter("batch_size", self.config.LLM_SERVER_BATCH_SIZE, "int")

            # Client 参数
            self.db_config.set_parameter("temperature", self.config.LLM_CLIENT_TEMPERATURE, "float")
            self.db_config.set_parameter("repeat_penalty", self.config.LLM_CLIENT_REPEAT_PENALTY, "float")
            self.db_config.set_parameter("max_tokens", self.config.LLM_CLIENT_MAX_TOKENS, "int")

            # System prompt
            self.db_config.set_parameter("system_prompt", self.config.DEFAULT_SYSTEM_PROMPT, "text")

            logger.info("✓ 默认参数已初始化:")
            logger.info(f"  Server: context_size={self.config.LLM_SERVER_CONTEXT_SIZE}, "
                       f"threads={self.config.LLM_SERVER_THREADS}, "
                       f"gpu_layers={self.config.LLM_SERVER_GPU_LAYERS}, "
                       f"batch_size={self.config.LLM_SERVER_BATCH_SIZE}")
            logger.info(f"  Client: temperature={self.config.LLM_CLIENT_TEMPERATURE}, "
                       f"repeat_penalty={self.config.LLM_CLIENT_REPEAT_PENALTY}, "
                       f"max_tokens={self.config.LLM_CLIENT_MAX_TOKENS}")
            logger.info(f"  System prompt: {self.config.DEFAULT_SYSTEM_PROMPT[:50]}...")

        except Exception as e:
            logger.error(f"✗ 初始化默认参数失败: {e}", exc_info=True)

    def _load_parameters_from_db(self):
        """
        从数据库加载所有模式的参数配置
        如果数据库中存在参数，优先使用数据库的值覆盖默认配置
        """
        logger.info("→ 加载参数配置...")

        try:
            # 尝试从数据库获取参数
            all_params = self.db_config.get_all_parameters()

            if not all_params:
                logger.info("ℹ 数据库中无参数配置，使用 config.py 默认值")
                return

            # 为每个模式加载参数
            for mode in ['llm', 'embed', 'rerank']:
                server = self.server_manager.get_server(mode)
                client = self.server_manager.get_client(mode)

                # Server 参数
                server_params_loaded = []
                if 'context_size' in all_params:
                    server.context_size = all_params['context_size']
                    server_params_loaded.append(f"context_size={all_params['context_size']}")
                if 'threads' in all_params:
                    server.threads = all_params['threads']
                    server_params_loaded.append(f"threads={all_params['threads']}")
                if 'gpu_layers' in all_params:
                    server.gpu_layers = all_params['gpu_layers']
                    server_params_loaded.append(f"gpu_layers={all_params['gpu_layers']}")
                if 'batch_size' in all_params:
                    server.batch_size = all_params['batch_size']
                    server_params_loaded.append(f"batch_size={all_params['batch_size']}")

                # Client 参数（仅 LLM 模式）
                client_params_loaded = []
                if mode == 'llm':
                    if 'temperature' in all_params:
                        client.temperature = all_params['temperature']
                        client_params_loaded.append(f"temperature={all_params['temperature']}")
                    if 'repeat_penalty' in all_params:
                        client.repeat_penalty = all_params['repeat_penalty']
                        client_params_loaded.append(f"repeat_penalty={all_params['repeat_penalty']}")
                    if 'max_tokens' in all_params:
                        client.max_tokens = all_params['max_tokens']
                        client_params_loaded.append(f"max_tokens={all_params['max_tokens']}")

                # 日志输出
                if server_params_loaded or client_params_loaded:
                    logger.info(f"✓ [{mode.upper()}] 从数据库加载参数配置:")
                    if server_params_loaded:
                        logger.info(f"  Server: {', '.join(server_params_loaded)}")
                    if client_params_loaded:
                        logger.info(f"  Client: {', '.join(client_params_loaded)}")

        except Exception as e:
            logger.warning(f"⚠ 加载参数配置失败: {e}")
            logger.info("  将使用 config.py 默认值")

    async def _start_all_current_models(self):
        """
        启动所有 is_current=true 的模型（LLM, Embed, Rerank）
        """
        logger.info("→ 检查并启动当前模型...")

        modes = ['llm', 'embed', 'rerank']
        started_count = 0

        for mode in modes:
            try:
                # 获取当前模型
                current_model = self.db_config.get_current_model(mode=mode)

                if not current_model:
                    logger.info(f"ℹ [{mode.upper()}] 未设置当前模型")
                    continue

                # 检查文件是否存在
                model_path = Path(current_model["model_path"])
                if not model_path.exists():
                    logger.warning(f"⚠ [{mode.upper()}] 模型文件不存在:")
                    logger.warning(f"  Name: {current_model['model_name']}")
                    logger.warning(f"  Path: {current_model['model_path']}")
                    logger.info(f"  请通过 UI 下载模型")
                    continue

                # 检查 is_downloaded 状态
                if not current_model.get('is_downloaded', False):
                    logger.warning(f"⚠ [{mode.upper()}] 模型未下载:")
                    logger.warning(f"  Name: {current_model['model_name']}")
                    logger.info(f"  请通过 UI 下载模型")
                    continue

                # 启动模型
                logger.info(f"✓ [{mode.upper()}] 找到当前模型:")
                logger.info(f"  Name: {current_model['model_name']}")
                logger.info(f"  Path: {current_model['model_path']}")

                success = await self._start_model_for_mode(
                    mode=mode,
                    model_name=current_model['model_name'],
                    model_path=current_model['model_path']
                )

                if success:
                    started_count += 1

            except Exception as e:
                logger.error(f"✗ [{mode.upper()}] 启动模型失败: {e}", exc_info=True)

        # 总结
        if started_count == 0:
            logger.warning("⚠ 没有启动任何模型")
            logger.info("  请通过 UI 下载并选择模型")
        else:
            logger.info(f"✓ 成功启动 {started_count} 个模型")

    async def _start_model_for_mode(self, mode: str, model_name: str, model_path: str) -> bool:
        """
        为指定模式启动 llama-server

        Args:
            mode: 模式 ('llm', 'embed', 'rerank')
            model_name: 模型名称
            model_path: 模型路径

        Returns:
            是否成功启动
        """
        logger.info(f"→ [{mode.upper()}] 启动 llama-server...")
        logger.info(f"  Model: {model_name}")
        logger.info(f"  Path: {model_path}")

        try:
            server = self.server_manager.get_server(mode)
            success = await server.start(model_path, model_name)

            if success:
                logger.info(f"✓ [{mode.upper()}] llama-server 启动成功")
                return True
            else:
                logger.error(f"✗ [{mode.upper()}] llama-server 启动失败")
                logger.error("  请检查上面的日志")
                return False

        except Exception as e:
            logger.error(f"✗ [{mode.upper()}] 启动错误: {e}", exc_info=True)
            return False
