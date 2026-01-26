"""
Backend exit handler
Ensures llama-server processes are cleaned up when backend exits
"""

import logging
import atexit
import signal
import sys
import asyncio

logger = logging.getLogger(__name__)


class BackendExitHandler:
    """Handle cleanup when backend exits"""

    def __init__(self, server_manager):
        """
        Initialize exit handler

        Args:
            server_manager: ModelServerManager instance to clean up
        """
        self.server_manager = server_manager
        self._registered = False

    def register(self):
        """Register cleanup handlers"""
        if self._registered:
            return

        # Register atexit handler for normal exit
        atexit.register(self._cleanup)

        # Register signal handlers for termination signals
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        self._registered = True
        logger.info("Registered backend exit handlers")

    def _cleanup(self):
        """Cleanup function called on exit"""
        logger.info("Backend exiting, cleaning up all llama-server processes...")
        try:
            # Stop all model servers
            asyncio.run(self.server_manager.stop_all())
            logger.info("✓ All llama-server processes stopped")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def _signal_handler(self, signum, frame):
        """Handle termination signals"""
        signal_name = signal.Signals(signum).name
        logger.info(f"Received signal {signal_name}, cleaning up...")
        self._cleanup()
        sys.exit(0)

