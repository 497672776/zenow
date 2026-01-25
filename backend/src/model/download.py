"""
Model download manager with progress tracking
"""
import httpx
import asyncio
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class ModelDownloader:
    """Model downloader with progress tracking"""

    def __init__(self, download_dir: Path):
        """
        Initialize model downloader

        Args:
            download_dir: Directory to save downloaded models
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.active_downloads: Dict[str, Dict[str, Any]] = {}

    def _get_filename_from_url(self, url: str) -> str:
        """
        Extract filename from URL

        Args:
            url: Download URL

        Returns:
            Filename extracted from URL
        """
        parsed = urlparse(url)
        filename = Path(parsed.path).name
        if not filename:
            filename = "model.gguf"
        return filename

    async def download_model(
        self,
        url: str,
        filename: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, float], None]] = None
    ) -> Path:
        """
        Download a model file with progress tracking

        Args:
            url: URL to download from
            filename: Optional custom filename (if not provided, extracted from URL)
            progress_callback: Optional callback function(downloaded_bytes, total_bytes, progress_percent)

        Returns:
            Path to the downloaded file

        Raises:
            Exception: If download fails
        """
        if filename is None:
            filename = self._get_filename_from_url(url)

        file_path = self.download_dir / filename

        # Check if file already exists
        if file_path.exists():
            logger.info(f"File already exists: {file_path}")
            if progress_callback:
                file_size = file_path.stat().st_size
                progress_callback(file_size, file_size, 100.0)
            return file_path

        # Register download
        download_id = url
        self.active_downloads[download_id] = {
            "url": url,
            "filename": filename,
            "status": "downloading",
            "downloaded": 0,
            "total": 0,
            "progress": 0.0
        }

        try:
            # Disable proxy for downloads (trust_env=False ignores system proxy)
            async with httpx.AsyncClient(
                timeout=None,
                follow_redirects=True,
                trust_env=False  # Ignore system proxy settings
            ) as client:
                async with client.stream('GET', url) as response:
                    response.raise_for_status()

                    total_size = int(response.headers.get('content-length', 0))
                    self.active_downloads[download_id]["total"] = total_size

                    downloaded = 0
                    with open(file_path, 'wb') as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            f.write(chunk)
                            downloaded += len(chunk)

                            # Update progress
                            self.active_downloads[download_id]["downloaded"] = downloaded
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                self.active_downloads[download_id]["progress"] = progress

                                if progress_callback:
                                    progress_callback(downloaded, total_size, progress)

            # Mark as completed
            self.active_downloads[download_id]["status"] = "completed"
            logger.info(f"Downloaded model to: {file_path}")
            return file_path

        except Exception as e:
            # Mark as failed
            self.active_downloads[download_id]["status"] = "failed"
            self.active_downloads[download_id]["error"] = str(e)

            # Clean up partial download
            if file_path.exists():
                file_path.unlink()

            logger.error(f"Failed to download model: {e}")
            raise

    def get_download_status(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get download status for a URL

        Args:
            url: Download URL

        Returns:
            Download status dict or None if not found
        """
        return self.active_downloads.get(url)

    def get_all_downloads(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all downloads

        Returns:
            Dictionary of all download statuses
        """
        return self.active_downloads.copy()
