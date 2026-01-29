#!/usr/bin/env python3
"""
MinIO功能测试脚本

测试内容：
1. MinIO服务器启动/停止/健康检查
2. MinIO客户端文件操作（上传/下载/删除/检查存在）
3. 文件夹操作（删除文件夹/检查文件夹存在）
4. 文件列表和URL生成

使用方法：
    python test_minio.py
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from spacemit_llm.comon.minio import MinioServerManager, MinioClientUtils

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title: str):
    """打印测试章节标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_test(test_name: str, success: bool, message: str = ""):
    """打印测试结果"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{test_name:<50} {status}")
    if message:
        print(f"   {message}")


async def test_minio_server():
    """测试MinIO服务器管理功能"""
    print_section("MinIO Server Management Tests")

    server = MinioServerManager()

    # 测试1: 健康检查（服务器未启动时）
    print("\n[Test 1] Health check (server not running)")
    is_running_before = server.health_check()
    print_test("Health check (before start)", not is_running_before,
               "Expected: False (server not running)")

    # 测试2: 启动服务器
    print("\n[Test 2] Start MinIO server")
    start_success = server.start()
    print_test("Start server", start_success)

    if start_success:
        # 测试3: 健康检查（服务器启动后）
        print("\n[Test 3] Health check (server running)")
        time.sleep(2)  # 等待服务器完全启动
        is_running_after = server.health_check()
        print_test("Health check (after start)", is_running_after,
                   "Expected: True (server running)")

        # 测试4: 重复启动（应该检测到已运行）
        print("\n[Test 4] Start server again (should detect already running)")
        start_again = server.start()
        print_test("Start server again", start_again,
                   "Should return True (already running)")

        # 测试5: 停止服务器
        print("\n[Test 5] Stop MinIO server")
        stop_success = server.stop()
        print_test("Stop server", stop_success)

        # 测试6: 健康检查（服务器停止后）
        print("\n[Test 6] Health check (after stop)")
        time.sleep(2)  # 等待服务器完全停止
        is_running_final = server.health_check()
        print_test("Health check (after stop)", not is_running_final,
                   "Expected: False (server stopped)")

    return start_success


async def test_minio_client():
    """测试MinIO客户端功能"""
    print_section("MinIO Client Operations Tests")

    # 确保服务器运行
    server = MinioServerManager()
    if not server.health_check():
        print("Starting MinIO server for client tests...")
        if not server.start():
            print("❌ Failed to start MinIO server for client tests")
            return False
        time.sleep(3)  # 等待服务器启动

    try:
        client = MinioClientUtils()

        # 测试数据
        test_file_name = "test-kb/doc-123/test-file.txt"
        test_file_content = b"This is a test file content for MinIO testing."
        test_folder_prefix = "test-kb/"

        # 测试1: 上传文件
        print("\n[Test 1] Upload file")
        try:
            uploaded_name = await client.upload_file(test_file_name, test_file_content)
            upload_success = uploaded_name == test_file_name
            print_test("Upload file", upload_success, f"Uploaded: {uploaded_name}")
        except Exception as e:
            print_test("Upload file", False, f"Error: {e}")
            return False

        # 测试2: 检查文件存在
        print("\n[Test 2] Check file exists")
        try:
            file_exists = await client.file_exists(test_file_name)
            print_test("File exists", file_exists, f"File exists: {file_exists}")
        except Exception as e:
            print_test("File exists", False, f"Error: {e}")

        # 测试3: 下载文件
        print("\n[Test 3] Download file")
        try:
            downloaded_content = await client.download_file(test_file_name)
            download_success = downloaded_content == test_file_content
            print_test("Download file", download_success,
                      f"Content match: {download_success}, Size: {len(downloaded_content)} bytes")
        except Exception as e:
            print_test("Download file", False, f"Error: {e}")

        # 测试4: 列出文件
        print("\n[Test 4] List files")
        try:
            files = await client.list_files(test_folder_prefix)
            list_success = len(files) > 0 and any(f["name"] == test_file_name for f in files)
            print_test("List files", list_success,
                      f"Found {len(files)} files, target file in list: {list_success}")
            if files:
                for file_info in files:
                    print(f"   - {file_info['name']} ({file_info['size']} bytes)")
        except Exception as e:
            print_test("List files", False, f"Error: {e}")

        # 测试5: 生成文件URL
        print("\n[Test 5] Generate file URL")
        try:
            file_url = await client.get_file_url(test_file_name, expiration_days=1)
            url_success = file_url.startswith("http") and test_file_name in file_url
            print_test("Generate file URL", url_success, f"URL generated: {url_success}")
            if url_success:
                print(f"   URL: {file_url[:100]}...")
        except Exception as e:
            print_test("Generate file URL", False, f"Error: {e}")

        # 测试6: 检查文件夹存在
        print("\n[Test 6] Check folder exists")
        try:
            folder_exists = await client.folder_exists(test_folder_prefix)
            print_test("Folder exists", folder_exists, f"Folder exists: {folder_exists}")
        except Exception as e:
            print_test("Folder exists", False, f"Error: {e}")

        # 测试7: 上传更多文件到同一文件夹
        print("\n[Test 7] Upload additional files")
        additional_files = [
            ("test-kb/doc-123/file2.txt", b"Second test file"),
            ("test-kb/doc-456/file3.txt", b"Third test file"),
        ]

        upload_count = 0
        for file_name, content in additional_files:
            try:
                await client.upload_file(file_name, content)
                upload_count += 1
            except Exception as e:
                print(f"   Failed to upload {file_name}: {e}")

        print_test("Upload additional files", upload_count == len(additional_files),
                   f"Uploaded {upload_count}/{len(additional_files)} files")

        # 测试8: 删除单个文件
        print("\n[Test 8] Delete single file")
        try:
            delete_success = await client.delete_file(test_file_name)
            print_test("Delete single file", delete_success)

            # 验证文件已删除
            file_exists_after_delete = await client.file_exists(test_file_name)
            print_test("Verify file deleted", not file_exists_after_delete,
                      f"File exists after delete: {file_exists_after_delete}")
        except Exception as e:
            print_test("Delete single file", False, f"Error: {e}")

        # 测试9: 删除整个文件夹
        print("\n[Test 9] Delete folder")
        try:
            deleted_count = await client.delete_folder(test_folder_prefix)
            delete_folder_success = deleted_count > 0
            print_test("Delete folder", delete_folder_success,
                      f"Deleted {deleted_count} files")

            # 验证文件夹已删除
            folder_exists_after_delete = await client.folder_exists(test_folder_prefix)
            print_test("Verify folder deleted", not folder_exists_after_delete,
                      f"Folder exists after delete: {folder_exists_after_delete}")
        except Exception as e:
            print_test("Delete folder", False, f"Error: {e}")

        return True

    except Exception as e:
        print_test("Client initialization", False, f"Error: {e}")
        return False


async def main():
    """主测试函数"""
    print("🧪 MinIO Functionality Test Suite")
    print("=" * 80)

    # 测试服务器管理
    server_success = await test_minio_server()

    # 测试客户端功能
    client_success = await test_minio_client()

    # 总结
    print_section("Test Summary")
    print_test("Server Management Tests", server_success)
    print_test("Client Operations Tests", client_success)

    overall_success = server_success and client_success
    print(f"\n{'🎉 All tests passed!' if overall_success else '❌ Some tests failed!'}")

    # 清理：确保服务器停止
    print("\n🧹 Cleanup: Stopping MinIO server...")
    server = MinioServerManager()
    server.stop()

    return overall_success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        # 清理
        server = MinioServerManager()
        server.stop()
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {e}")
        sys.exit(1)