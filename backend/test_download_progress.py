#!/usr/bin/env python3
"""
测试下载进度 API
"""
import asyncio
import httpx
import time

BASE_URL = "http://localhost:8050"


async def test_download_progress():
    """测试下载进度功能"""

    # 测试 URL（一个小文件用于测试）
    test_url = "https://modelscope.cn/models/second-state/Qwen2.5-0.5B-Instruct-GGUF/resolve/master/Qwen2.5-0.5B-Instruct-Q4_0.gguf"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 启动下载
        print("=" * 60)
        print("1. 启动下载")
        print("=" * 60)

        response = await client.post(
            f"{BASE_URL}/api/models/download",
            json={
                "url": test_url,
                "mode": "llm"
            }
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        print()

        # 2. 轮询下载进度
        print("=" * 60)
        print("2. 查询下载进度")
        print("=" * 60)

        for i in range(10):
            await asyncio.sleep(2)  # 每 2 秒查询一次

            response = await client.get(
                f"{BASE_URL}/api/models/download/status",
                params={"url": test_url}
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    download = data.get("download", {})
                    status = download.get("status", "unknown")
                    progress = download.get("progress", 0)
                    downloaded = download.get("downloaded", 0)
                    total = download.get("total", 0)

                    print(f"[{i+1}] 状态: {status} | 进度: {progress:.2f}% | "
                          f"已下载: {downloaded / 1024 / 1024:.2f}MB / {total / 1024 / 1024:.2f}MB")

                    if status == "completed":
                        print("\n✓ 下载完成！")
                        break
                    elif status == "failed":
                        print(f"\n✗ 下载失败: {download.get('error')}")
                        break
                else:
                    print(f"[{i+1}] 未找到下载记录")
            else:
                print(f"[{i+1}] API 错误: {response.status_code}")

        print()

        # 3. 获取所有下载状态
        print("=" * 60)
        print("3. 获取所有下载状态")
        print("=" * 60)

        response = await client.get(f"{BASE_URL}/api/models/download/status")
        if response.status_code == 200:
            data = response.json()
            downloads = data.get("downloads", {})
            print(f"活跃下载数量: {len(downloads)}")
            for url, info in downloads.items():
                print(f"\nURL: {url}")
                print(f"  状态: {info.get('status')}")
                print(f"  进度: {info.get('progress', 0):.2f}%")
                print(f"  文件名: {info.get('filename')}")


if __name__ == "__main__":
    print("测试下载进度 API")
    print("确保后端服务正在运行: http://localhost:8050")
    print()

    try:
        asyncio.run(test_download_progress())
    except KeyboardInterrupt:
        print("\n\n测试中断")
    except Exception as e:
        print(f"\n错误: {e}")
