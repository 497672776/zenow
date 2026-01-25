"""
Backend exit handler
Ensures llama-server processes are cleaned up when backend exits
"""

import logging
import atexit
import signal
import sys

logger = logging.getLogger(__name__)


class BackendExitHandler:
    """Handle cleanup when backend exits"""

    def __init__(self, llm_server):
        """
        Initialize exit handler

        Args:
            llm_server: LLMServer instance to clean up
        """
        self.llm_server = llm_server
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
        logger.info("Backend exiting, cleaning up llama-server...")
        try:
            # Stop the LLM server if running
            self.llm_server.stop_server()

            # Additional cleanup: kill any remaining llama-server processes
            # This catches any orphaned or zombie processes
            # import subprocess
            # try:
            #     result = subprocess.run(
            #         ["pkill", "-9", "llama-server"],
            #         capture_output=True,
            #         text=True
            #     )
            #     if result.returncode == 0:
            #         logger.info("✓ Killed any remaining llama-server processes")
            # except Exception as e:
            #     logger.debug(f"pkill command failed (this is OK if no processes): {e}")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def _signal_handler(self, signum, frame):
        """Handle termination signals"""
        signal_name = signal.Signals(signum).name
        logger.info(f"Received signal {signal_name}, cleaning up...")
        self._cleanup()
        sys.exit(0)
