"""
Port file management utilities
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def write_port_file(port: int, port_file_path: str = None):
    """
    Write the port number to a file for frontend to read.

    Args:
        port: The port number to write
        port_file_path: Optional custom path for the port file.
                       If None, uses default ~/.config/zenow/backend.port
    """
    if port_file_path:
        port_file = Path(port_file_path)
    else:
        port_file = Path.home() / ".config" / "zenow" / "backend.port"

    port_file.parent.mkdir(parents=True, exist_ok=True)

    # Write port to file for frontend discovery
    port_file.write_text(f"{port}\n")
    logger.info(f"📝 Wrote port {port} to {port_file}")


def cleanup_port_file(port_file_path: str = None):
    """
    Remove port file on shutdown.

    Args:
        port_file_path: Optional custom path for the port file.
                       If None, uses default ~/.config/zenow/backend.port
    """
    if port_file_path:
        port_file = Path(port_file_path)
    else:
        port_file = Path.home() / ".config" / "zenow" / "backend.port"

    if port_file.exists():
        port_file.unlink()
        logger.info(f"🧹 Cleaned up port file: {port_file}")