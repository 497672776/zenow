"""
模型下载管理器，支持进度追踪
"""
import httpx
import asyncio
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class ModelDownloader:
    """模型下载器，支持进度追踪"""

    def __init__(self, download_dir: Path):
        """
        初始化模型下载器

        Args:
            download_dir: 保存下载模型的目录
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.active_downloads: Dict[str, Dict[str, Any]] = {}

    def _get_filename_from_url(self, url: str) -> str:
        """
        从URL中提取文件名

        Args:
            url: 下载URL

        Returns:
            从URL中提取的文件名
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
        下载模型文件，支持进度追踪，使用临时文件

        Args:
            url: 下载URL
            filename: 可选的自定义文件名（如果未提供，则从URL中提取）
            progress_callback: 可选的回调函数(已下载字节数, 总字节数, 进度百分比)

        Returns:
            下载文件的路径

        Raises:
            Exception: 如果下载失败
        """
        if filename is None:
            filename = self._get_filename_from_url(url)

        file_path = self.download_dir / filename
        temp_path = file_path.with_suffix(file_path.suffix + '.tmp')

        # 检查文件是否已存在且完整
        if file_path.exists():
            logger.info(f"文件已存在: {file_path}")
            if progress_callback:
                file_size = file_path.stat().st_size
                progress_callback(file_size, file_size, 100.0)
            return file_path

        # 检查是否有未完成的下载
        if temp_path.exists():
            logger.warning(f"发现未完成的下载，正在删除: {temp_path}")
            temp_path.unlink()

        # 注册下载任务
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
            # 禁用代理进行下载（trust_env=False 忽略系统代理）
            async with httpx.AsyncClient(
                timeout=None,
                follow_redirects=True,
                trust_env=False  # 忽略系统代理设置
            ) as client:
                async with client.stream('GET', url) as response:
                    response.raise_for_status()

                    total_size = int(response.headers.get('content-length', 0))
                    self.active_downloads[download_id]["total"] = total_size

                    downloaded = 0
                    # 下载到临时文件
                    with open(temp_path, 'wb') as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            f.write(chunk)
                            downloaded += len(chunk)

                            # 更新进度
                            self.active_downloads[download_id]["downloaded"] = downloaded
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                self.active_downloads[download_id]["progress"] = progress

                                if progress_callback:
                                    progress_callback(downloaded, total_size, progress)

            # 如果提供了总大小，验证文件大小
            if total_size > 0:
                actual_size = temp_path.stat().st_size
                if actual_size != total_size:
                    raise Exception(
                        f"下载不完整: 期望 {total_size} 字节，实际 {actual_size} 字节"
                    )

            # 将临时文件重命名为最终文件（原子操作）
            temp_path.rename(file_path)

            # 标记为已完成
            self.active_downloads[download_id]["status"] = "completed"
            logger.info(f"模型已下载到: {file_path}")
            return file_path

        except Exception as e:
            # 标记为失败
            self.active_downloads[download_id]["status"] = "failed"
            self.active_downloads[download_id]["error"] = str(e)

            # 清理临时文件
            if temp_path.exists():
                temp_path.unlink()
                logger.info(f"已清理临时文件: {temp_path}")

            logger.error(f"模型下载失败: {e}")
            raise

    def get_download_status(self, url: str) -> Optional[Dict[str, Any]]:
        """
        获取指定URL的下载状态

        Args:
            url: 下载URL

        Returns:
            下载状态字典，如果未找到则返回None
        """
        return self.active_downloads.get(url)

    def get_all_downloads(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all downloads

        Returns:
            Dictionary of all download statuses
        """
        return self.active_downloads.copy()
