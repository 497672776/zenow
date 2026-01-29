"""
MinIO server management and client utilities for document storage.

Architecture:
- MinioServerManager: Server lifecycle management (start/stop/health)
- MinioClientUtils: File operations (upload/download/delete/exists)

Usage:
    # Server management
    server = MinioServerManager()
    server.start()
    server.health_check()
    server.stop()

    # Client operations
    client = MinioClientUtils()
    await client.upload_file("my-kb/doc-123/report.pdf", file_content)
    content = await client.download_file("my-kb/doc-123/report.pdf")
    await client.delete_file("my-kb/doc-123/report.pdf")
"""

import logging
import os
import subprocess
import time
import requests
import asyncio
from io import BytesIO
from typing import Optional, List, Dict, Any
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)


# ============================================================================
# MinIO Server Manager
# ============================================================================

class MinioServer:
    """MinIO server lifecycle management."""

    def __init__(
        self,
        endpoint: str = "localhost:9000",
        console_port: int = 9001,
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin",
        data_dir: str = None
    ):
        """Initialize MinIO server manager.

        Args:
            endpoint: MinIO server endpoint (default: localhost:9000)
            console_port: MinIO console port (default: 9001)
            access_key: MinIO access key (default: minioadmin)
            secret_key: MinIO secret key (default: minioadmin)
            data_dir: Data storage directory (default: ~/.cache/rag_chat/documents)
        """
        self.endpoint = endpoint
        self.console_port = console_port
        self.access_key = access_key
        self.secret_key = secret_key
        self.data_dir = data_dir or os.path.expanduser("~/.cache/rag_chat/documents")
        self.process: Optional[subprocess.Popen] = None

    def find_minio_binary(self) -> Optional[str]:
        """Find MinIO binary in common locations.

        Returns:
            Path to minio binary or None if not found
        """
        common_paths = [
            "/usr/local/bin/minio",
            "/usr/bin/minio",
            os.path.expanduser("~/minio"),
            os.path.expanduser("~/minio-server/minio"),
            os.path.expanduser("~/.local/bin/minio"),
            "/opt/minio/minio",
        ]

        # Check if 'minio' is in PATH
        try:
            result = subprocess.run(["which", "minio"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                path = result.stdout.strip()
                if path:
                    logger.info(f"Found MinIO in PATH: {path}")
                    return path
        except Exception as e:
            logger.debug(f"Failed to check PATH for minio: {e}")

        # Check common paths
        for path in common_paths:
            if os.path.exists(path) and os.path.isfile(path):
                logger.info(f"Found MinIO binary at: {path}")
                return path

        return None

    def health_check(self) -> bool:
        """Check if MinIO server is running and healthy.

        Returns:
            True if MinIO is running and healthy, False otherwise
        """
        try:
            response = requests.get(
                f"http://{self.endpoint}/minio/health/live",
                timeout=2
            )
            is_healthy = response.status_code == 200
            if is_healthy:
                logger.debug(f"MinIO health check passed: {self.endpoint}")
            else:
                logger.warning(f"MinIO health check failed: {response.status_code}")
            return is_healthy
        except (requests.ConnectionError, requests.Timeout) as e:
            logger.debug(f"MinIO health check failed: {e}")
            return False

    def start(self) -> bool:
        """Start MinIO server.

        Returns:
            True if started successfully, False otherwise
        """
        # Check if already running
        if self.health_check():
            logger.info(f"✅ MinIO server already running at {self.endpoint}")
            return True

        # Find binary
        minio_binary = self.find_minio_binary()
        if not minio_binary:
            logger.error("❌ MinIO binary not found. Please install MinIO:")
            logger.error("   wget https://dl.min.io/server/minio/release/linux-amd64/minio -O ~/.local/bin/minio")
            logger.error("   chmod +x ~/.local/bin/minio")
            return False

        # Create data directory
        os.makedirs(self.data_dir, exist_ok=True)

        # Prepare environment
        env = os.environ.copy()
        env["MINIO_ROOT_USER"] = self.access_key
        env["MINIO_ROOT_PASSWORD"] = self.secret_key

        try:
            logger.info("🚀 Starting MinIO server...")
            logger.info(f"   Binary: {minio_binary}")
            logger.info(f"   Data directory: {self.data_dir}")
            logger.info(f"   Endpoint: http://{self.endpoint}")
            logger.info(f"   Console: http://localhost:{self.console_port}")

            # Start process
            self.process = subprocess.Popen(
                [minio_binary, "server", self.data_dir, "--console-address", f":{self.console_port}"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait for startup (up to 30 seconds)
            logger.info("⏳ Waiting for MinIO to start...")
            for _ in range(30):
                time.sleep(1)
                if self.health_check():
                    logger.info("✅ MinIO server started successfully!")
                    logger.info(f"   Endpoint: http://{self.endpoint}")
                    logger.info(f"   Console: http://localhost:{self.console_port}")
                    logger.info(f"   Username: {self.access_key}")
                    logger.info(f"   Password: {self.secret_key}")
                    return True

            # Failed to start
            logger.error("❌ MinIO failed to start within 30 seconds")
            self._capture_error_output()
            return False

        except Exception as e:
            logger.error(f"❌ Failed to start MinIO: {e}")
            return False

    def stop(self) -> bool:
        """Stop MinIO server.

        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.process:
            logger.info("MinIO server is not running")
            return True

        try:
            logger.info("🛑 Stopping MinIO server...")
            self.process.terminate()

            # Wait for graceful shutdown (up to 10 seconds)
            try:
                self.process.wait(timeout=10)
                logger.info("✅ MinIO server stopped successfully")
            except subprocess.TimeoutExpired:
                logger.warning("⚠️ MinIO did not stop gracefully, killing process...")
                self.process.kill()
                self.process.wait()
                logger.info("✅ MinIO server killed")

            return True

        except Exception as e:
            logger.error(f"Error stopping MinIO: {e}")
            return False
        finally:
            self.process = None

    def _capture_error_output(self):
        """Capture and log error output from MinIO process."""
        try:
            if self.process and self.process.poll() is not None:
                stdout, stderr = self.process.communicate(timeout=1)
                if stderr:
                    logger.error(f"   MinIO stderr: {stderr[:500]}")
                if stdout:
                    logger.error(f"   MinIO stdout: {stdout[:500]}")
            else:
                logger.error("   MinIO process is running but not responding")
        except Exception as e:
            logger.error(f"   Could not capture MinIO output: {e}")


# ============================================================================
# MinIO Client Utils
# ============================================================================

class MinioClient:
    """MinIO client utilities for file operations."""

    def __init__(
        self,
        endpoint: str = "localhost:9000",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin",
        bucket_name: str = "rag-documents",
        secure: bool = False
    ):
        """Initialize MinIO client utilities.

        Args:
            endpoint: MinIO server endpoint (default: localhost:9000)
            access_key: MinIO access key (default: minioadmin)
            secret_key: MinIO secret key (default: minioadmin)
            bucket_name: Default bucket name (default: rag-documents)
            secure: Use HTTPS (default: False)
        """
        self.endpoint = endpoint
        self.bucket_name = bucket_name

        try:
            self.client = Minio(
                endpoint=endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure,
            )

            # Ensure bucket exists
            self._ensure_bucket_exists()
            logger.info(f"✅ MinIO client initialized: {endpoint}/{bucket_name}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize MinIO client: {e}")
            raise

    def _ensure_bucket_exists(self):
        """Ensure the bucket exists, create if not."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"✅ Created MinIO bucket: {self.bucket_name}")
            else:
                logger.debug(f"✅ MinIO bucket exists: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            raise

    async def upload_file(self, object_name: str, file_content: bytes) -> str:
        """Upload file to MinIO.

        Args:
            object_name: Object path (e.g., "my-kb/doc-123/report.pdf")
            file_content: File content as bytes

        Returns:
            Object name in MinIO

        Raises:
            Exception: If upload fails
        """
        try:
            file_size = len(file_content)
            file_stream = BytesIO(file_content)

            # Run blocking operation in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.client.put_object,
                self.bucket_name,
                object_name,
                file_stream,
                file_size,
                "application/octet-stream"
            )

            logger.info(f"✅ Uploaded: {self.bucket_name}/{object_name} ({file_size} bytes)")
            return object_name

        except S3Error as e:
            logger.error(f"❌ Upload failed: {object_name} - {e}")
            raise

    async def download_file(self, object_name: str) -> bytes:
        """Download file from MinIO.

        Args:
            object_name: Object path (e.g., "my-kb/doc-123/report.pdf")

        Returns:
            File content as bytes

        Raises:
            Exception: If download fails
        """
        try:
            loop = asyncio.get_event_loop()
            content: bytes = await loop.run_in_executor(
                None,
                self._download_file_blocking,
                object_name,
            )

            logger.info(f"✅ Downloaded: {self.bucket_name}/{object_name} ({len(content)} bytes)")
            return content

        except S3Error as e:
            logger.error(f"❌ Download failed: {object_name} - {e}")
            raise

    def _download_file_blocking(self, object_name: str) -> bytes:
        """Blocking download implementation."""
        response = self.client.get_object(self.bucket_name, object_name)
        try:
            content = response.read()
        finally:
            response.close()
            response.release_conn()
        return content

    async def delete_file(self, object_name: str) -> bool:
        """Delete single file from MinIO.

        Args:
            object_name: Object path (e.g., "my-kb/doc-123/report.pdf")

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"✅ Deleted file: {self.bucket_name}/{object_name}")
            return True

        except S3Error as e:
            logger.error(f"❌ Delete file failed: {object_name} - {e}")
            return False

    async def delete_folder(self, prefix: str) -> int:
        """Delete all files with given prefix (folder).

        Args:
            prefix: Folder prefix (e.g., "my-kb/" or "my-kb/doc-123/")

        Returns:
            Number of files deleted
        """
        try:
            objects = self.client.list_objects(self.bucket_name, prefix=prefix)
            delete_count = 0

            for obj in objects:
                self.client.remove_object(self.bucket_name, obj.object_name)
                delete_count += 1

            logger.info(f"✅ Deleted folder: {self.bucket_name}/{prefix} ({delete_count} files)")
            return delete_count

        except S3Error as e:
            logger.error(f"❌ Delete folder failed: {prefix} - {e}")
            return 0

    async def file_exists(self, object_name: str) -> bool:
        """Check if file exists in MinIO.

        Args:
            object_name: Object path (e.g., "my-kb/doc-123/report.pdf")

        Returns:
            True if file exists, False otherwise
        """
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False

    async def folder_exists(self, prefix: str) -> bool:
        """Check if folder exists (has any objects with prefix).

        Args:
            prefix: Folder prefix (e.g., "my-kb/" or "my-kb/doc-123/")

        Returns:
            True if folder exists (has objects), False otherwise
        """
        try:
            objects = self.client.list_objects(self.bucket_name, prefix=prefix, max_keys=1)
            # If we can get at least one object, folder exists
            for _ in objects:
                return True
            return False
        except S3Error:
            return False

    async def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List files in MinIO with optional prefix filter.

        Args:
            prefix: Optional prefix filter (e.g., "my-kb/")

        Returns:
            List of file info dictionaries with keys: name, size, last_modified
        """
        try:
            objects = self.client.list_objects(self.bucket_name, prefix=prefix)
            files = []

            for obj in objects:
                files.append({
                    "name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
                    "etag": obj.etag
                })

            logger.info(f"✅ Listed {len(files)} files with prefix: {prefix}")
            return files

        except S3Error as e:
            logger.error(f"❌ List files failed: {prefix} - {e}")
            return []

    async def get_file_url(self, object_name: str, expiration_days: int = 7) -> str:
        """Generate presigned URL for file download.

        Args:
            object_name: Object path (e.g., "my-kb/doc-123/report.pdf")
            expiration_days: URL expiration time in days (max 7)

        Returns:
            Presigned download URL
        """
        try:
            # Cap expiration to 7 days (MinIO limit)
            actual_expiration_days = min(expiration_days, 7)
            expiration = timedelta(days=actual_expiration_days)

            url = self.client.get_presigned_url(
                method='GET',
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=expiration
            )

            logger.info(f"✅ Generated URL for: {object_name} (expires in {actual_expiration_days} days)")
            return url

        except Exception as e:
            logger.error(f"❌ Generate URL failed: {object_name} - {e}")
            raise


