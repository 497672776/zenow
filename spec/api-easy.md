# Zenow API 简表

| 端点 | 方法 | 功能 | 请求体 | 响应示例 |
|------|------|------|--------|----------|
| `/api/models/current` | GET | 获取当前模型 | 无 | `{"id": 1, "name": "Qwen2.5-0.5B-Instruct-Q4_0", "path": "/home/user/.cache/zenow/models/llm/...", "is_downloaded": true, "mode": "llm"}` |
| `/api/models/load` | POST | 加载模型 | `{"model_name": "Qwen2.5-0.5B-Instruct-Q4_0", "download_url": "https://...", "mode": "llm"}` | `{"success": true, "message": "Model loaded successfully", "model_name": "...", "model_path": "...", "server_status": "running"}` |
| `/api/models/list` | GET | 获取模型列表 | 无 | `{"models": [...], "current_model": {...}}` |
| `/api/models/download` | POST | 下载模型 | `{"url": "https://...", "filename": "model.gguf", "mode": "llm"}` | `{"success": true, "url": "https://...", "mode": "llm", "message": "Download started"}` |
| `/api/models/download/status` | GET | 获取下载状态 | 无 | `{"success": true, "download": {"url": "...", "status": "downloading", "progress": 50.0}}` |
| `/api/models/get_param` | GET | 获取模型参数 | 无 | `{"context_size": 8192, "threads": 8, "temperature": 0.7, "max_tokens": 2048}` |
| `/api/models/update_param` | POST | 更新模型参数 | `{"context_size": 4096, "threads": 4, "temperature": 0.8}` | `{"success": true, "message": "Parameters updated successfully", "requires_restart": true}` |
| `/api/downloads/default-urls` | GET | 获取默认下载链接 | 无 | `{"urls": {"llm": [...], "embed": [...], "rerank": [...]}, "browser_path": "https://..."}` |
| `/api/sessions` | POST | 创建会话 | `{"first_message": "你好，请介绍一下自己"}` | `{"session_id": 1, "session_name": "你好，请介绍一下自己"}` |
| `/api/sessions/{session_id}` | DELETE | 删除会话 | 无 | `{"success": true, "message": "Session deleted"}` |
| `/api/sessions` | GET | 获取会话列表 | 无 | `{"sessions": [{"id": 1, "session_name": "...", "message_count": 4}], "total": 1}` |
| `/api/sessions/{session_id}` | GET | 获取会话详情 | 无 | `{"id": 1, "session_name": "...", "created_at": "...", "message_count": 4}` |
| `/api/sessions/{session_id}/name` | PUT | 更新会话名称 | `{"new_name": "关于 AI 的讨论"}` | `{"success": true, "message": "Session name updated"}` |
| `/api/sessions/{session_id}/messages` | GET | 获取会话消息 | 无 | `{"messages": [{"id": 1, "role": "user", "content": "..."}], "total_tokens": 256}` |
| `/api/sessions/{session_id}/messages` | POST | 添加消息到会话 | `{"role": "user", "content": "这是一条测试消息"}` | `{"message_id": 3, "token_count": 8}` |
| `/api/sessions/{session_id}/messages` | DELETE | 清空会话消息 | 无 | `{"success": true, "message": "Messages cleared"}` |
| `/api/chat` | POST | 流式聊天 | `{"messages": [{"role": "user", "content": "你好"}], "session_id": 1, "stream": true}` | SSE流: `data: {"choices":[{"delta":{"content":"你好"}}]}` ... `data: [DONE]` |
| `/api/server/status` | GET | 获取服务器状态 | 无 | `{"status": "running", "model_name": "...", "is_running": true}` |

## 说明

- **Base URL**: `http://localhost:8050`
- **数据格式**: JSON
- **流式响应**: Server-Sent Events (SSE)
- **模型模式**: `llm`、`embed`、`rerank`

## 查询参数

大部分端点支持 `mode` 查询参数来指定模型模式，例如：
- `GET /api/models/current?mode=llm`
- `GET /api/server/status?mode=embed`
- `POST /api/models/update_param?mode=rerank`
