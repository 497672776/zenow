#!/usr/bin/env python3
"""
MinIO使用示例

演示如何使用重构后的MinIO模块进行服务器管理和文件操作
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from spacemit_llm.comon.minio import MinioServerManager, MinioClientUtils


async def example_usage():
    """MinIO使用示例"""

    print("🚀 MinIO Usage Example")
    print("=" * 50)

    # 1. 服务器管理
    print("\n📋 Step 1: Server Management")
    server = MinioServerManager()

    print(f"   Server endpoint: {server.endpoint}")
    print(f"   Data directory: {server.data_dir}")
    print(f"   Health check: {server.health_check()}")

    # 2. 启动服务器（如果需要）
    print("\n📋 Step 2: Start Server (if needed)")
    if not server.health_check():
        print("   Starting MinIO server...")
        if server.start():
            print("   ✅ Server started successfully")
        else:
            print("   ❌ Failed to start server")
            return
    else:
        print("   ✅ Server already running")

    # 3. 客户端操作
    print("\n📋 Step 3: Client Operations")
    try:
        client = MinioClientUtils()
        print(f"   Client bucket: {client.bucket_name}")

        # 示例文件操作
        test_file = "example/test.txt"
        test_content = b"Hello MinIO from Zenow!"

        # 上传文件
        print(f"   Uploading file: {test_file}")
        await client.upload_file(test_file, test_content)

        # 检查文件存在
        exists = await client.file_exists(test_file)
        print(f"   File exists: {exists}")

        # 下载文件
        if exists:
            content = await client.download_file(test_file)
            print(f"   Downloaded content: {content.decode()}")

        # 生成URL
        url = await client.get_file_url(test_file, expiration_days=1)
        print(f"   File URL: {url[:50]}...")

        # 清理
        await client.delete_file(test_file)
        print(f"   File deleted")

    except Exception as e:
        print(f"   ❌ Client error: {e}")

    # 4. 停止服务器（可选）
    print("\n📋 Step 4: Server Management (optional)")
    print("   Server is still running for other operations...")
    print("   Use server.stop() to stop when done")


if __name__ == "__main__":
    asyncio.run(example_usage())