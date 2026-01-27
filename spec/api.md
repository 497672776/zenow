# Zenow API 文档

## 基本信息

- **Base URL**: `http://localhost:8050`
- **协议**: HTTP/HTTPS
- **数据格式**: JSON
- **流式响应**: Server-Sent Events (SSE)

---

## 1. 模型管理

### 1.1 获取当前模型

获取指定模式下的当前加载模型。

**请求**

```http
GET /api/models/current?mode={mode}
```

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| mode | string | 否 | llm | 模型模式：`llm`、`embed`、`rerank` |

**响应示例**

```json
{
  "id": 1,
  "name": "Qwen2.5-0.5B-Instruct-Q4_0",
  "path": "/home/user/.cache/zenow/models/llm/Qwen2.5-0.5B-Instruct-Q4_0.gguf",
  "is_downloaded": true,
  "mode": "llm"
}
```

**状态码**

- `200`: 成功
- `500`: 服务器错误

---

### 1.2 加载模型

加载指定模型（支持下载、切换、启动服务器）。

**请求**

```http
POST /api/models/load
Content-Type: application/json
```

**请求体**

```json
{
  "model_name": "Qwen2.5-0.5B-Instruct-Q4_0",
  "download_url": "https://example.com/model.gguf",
  "mode": "llm"
}
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model_name | string | 是 | 模型名称 |
| download_url | string | 否 | 下载链接（如果模型未下载） |
| mode | string | 否 | 模型模式，默认 `llm` |

**响应示例**

```json
{
  "success": true,
  "message": "Model loaded successfully",
  "model_name": "Qwen2.5-0.5B-Instruct-Q4_0",
  "model_path": "/home/user/.cache/zenow/models/llm/Qwen2.5-0.5B-Instruct-Q4_0.gguf",
  "server_status": "running"
}
```

---

### 1.3 获取模型列表

获取所有已添加的模型列表。

**请求**

```http
GET /api/models/list?mode={mode}
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| mode | string | 否 | 筛选特定模式的模型：`llm`、`embed`、`rerank` |

**响应示例**

```json
{
  "models": [
    {
      "id": 1,
      "name": "Qwen2.5-0.5B-Instruct-Q4_0",
      "path": "/home/user/.cache/zenow/models/llm/Qwen2.5-0.5B-Instruct-Q4_0.gguf",
      "is_downloaded": true,
      "mode": "llm"
    },
    {
      "id": 2,
      "name": "bge-small-zh-v1.5",
      "path": "/home/user/.cache/zenow/models/embed/bge-small-zh-v1.5.gguf",
      "is_downloaded": false,
      "mode": "embed"
    }
  ],
  "current_model": {
    "id": 1,
    "name": "Qwen2.5-0.5B-Instruct-Q4_0",
    "path": "/home/user/.cache/zenow/models/llm/Qwen2.5-0.5B-Instruct-Q4_0.gguf",
    "is_downloaded": true,
    "mode": "llm"
  }
}
```

---

### 1.4 下载模型

下载模型文件（仅下载，不切换）。

**请求**

```http
POST /api/models/download
Content-Type: application/json
```

**请求体**

```json
{
  "url": "https://modelscope.cn/models/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/master/qwen2.5-0.5b-instruct-q4_0.gguf",
  "filename": "Qwen2.5-0.5B-Instruct-Q4_0.gguf",
  "mode": "llm"
}
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| url | string | 是 | 模型下载链接 |
| filename | string | 否 | 保存的文件名（不指定则从 URL 提取） |
| mode | string | 否 | 模型模式，默认 `llm` |

**响应示例**

```json
{
  "success": true,
  "url": "https://modelscope.cn/models/...",
  "mode": "llm",
  "message": "Download started"
}
```

---

### 1.5 获取下载状态

查询模型下载进度。

**请求**

```http
GET /api/models/download/status?url={url}
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| url | string | 否 | 指定 URL 的下载状态（不提供则返回所有下载） |

**响应示例（单个下载）**

```json
{
  "success": true,
  "download": {
    "url": "https://modelscope.cn/models/...",
    "filename": "Qwen2.5-0.5B-Instruct-Q4_0.gguf",
    "status": "downloading",
    "downloaded": 52428800,
    "total": 104857600,
    "progress": 50.0,
    "error": null
  }
}
```

**响应示例（所有下载）**

```json
{
  "success": true,
  "downloads": [
    {
      "url": "https://modelscope.cn/models/...",
      "filename": "Qwen2.5-0.5B-Instruct-Q4_0.gguf",
      "status": "completed",
      "downloaded": 104857600,
      "total": 104857600,
      "progress": 100.0,
      "error": null
    }
  ]
}
```

**状态值说明**

- `downloading`: 下载中
- `completed`: 下载完成
- `failed`: 下载失败

---

### 1.6 获取模型参数

获取指定模式的模型参数配置。

**请求**

```http
GET /api/models/get_param?mode={mode}
```

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| mode | string | 否 | llm | 模型模式：`llm`、`embed`、`rerank` |

**响应示例（LLM 模式）**

```json
{
  "context_size": 8192,
  "threads": 8,
  "gpu_layers": 0,
  "batch_size": 512,
  "temperature": 0.7,
  "repeat_penalty": 1.1,
  "max_tokens": 2048
}
```

**响应示例（Embed 模式）**

```json
{
  "context_size": 8192,
  "threads": 8,
  "gpu_layers": 0,
  "batch_size": 512,
  "normalize": true,
  "truncate": true
}
```

---

### 1.7 更新模型参数

更新指定模式的模型参数（如需重启服务器会自动处理）。

**请求**

```http
POST /api/models/update_param?mode={mode}
Content-Type: application/json
```

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| mode | string | 否 | llm | 模型模式：`llm`、`embed`、`rerank` |

**请求体（LLM 模式）**

```json
{
  "context_size": 4096,
  "threads": 4,
  "gpu_layers": 0,
  "batch_size": 512,
  "temperature": 0.8,
  "repeat_penalty": 1.2,
  "max_tokens": 1024
}
```

**参数说明**

| 参数 | 类型 | 说明 | 是否需要重启服务器 |
|------|------|------|-------------------|
| context_size | integer | 上下文窗口大小 | 是 |
| threads | integer | CPU 线程数 | 是 |
| gpu_layers | integer | GPU 层数 | 是 |
| batch_size | integer | 批处理大小 | 是 |
| temperature | float | 温度参数（LLM） | 否 |
| repeat_penalty | float | 重复惩罚（LLM） | 否 |
| max_tokens | integer | 最大生成 token 数（LLM） | 否 |

**响应示例**

```json
{
  "success": true,
  "message": "Parameters updated successfully",
  "requires_restart": true
}
```

---

### 1.8 获取默认下载链接

获取预配置的默认模型下载链接。

**请求**

```http
GET /api/downloads/default-urls
```

**响应示例**

```json
{
  "urls": {
    "llm": [
      "https://modelscope.cn/models/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/master/qwen2.5-0.5b-instruct-q4_0.gguf",
      "https://modelscope.cn/models/unsloth/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q4_K_M.gguf"
    ],
    "embed": [
      "https://modelscope.cn/models/AI-ModelScope/bge-small-zh-v1.5-gguf/resolve/master/bge-small-zh-v1.5-q4_0.gguf"
    ],
    "rerank": [
      "https://modelscope.cn/models/AI-ModelScope/bge-reranker-v2-m3-gguf/resolve/master/bge-reranker-v2-m3-q4_0.gguf"
    ]
  },
  "browser_path": "https://modelscope.cn/models"
}
```

---

## 2. 会话管理

### 2.1 创建会话

创建新的聊天会话。

**请求**

```http
POST /api/sessions
Content-Type: application/json
```

**请求体**

```json
{
  "first_message": "你好，请介绍一下自己"
}
```

**响应示例**

```json
{
  "session_id": 1,
  "session_name": "你好，请介绍一下自己"
}
```

---

### 2.2 删除会话

删除指定会话（级联删除所有消息）。

**请求**

```http
DELETE /api/sessions/{session_id}
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | integer | 会话 ID |

**响应示例**

```json
{
  "success": true,
  "message": "Session deleted"
}
```

**状态码**

- `200`: 删除成功
- `404`: 会话不存在
- `500`: 服务器错误

---

### 2.3 获取会话列表

获取所有会话列表，按更新时间倒序排列。

**请求**

```http
GET /api/sessions?limit={limit}&offset={offset}
```

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| limit | integer | 否 | 100 | 返回的最大会话数 |
| offset | integer | 否 | 0 | 偏移量（用于分页） |

**响应示例**

```json
{
  "sessions": [
    {
      "id": 1,
      "session_name": "你好，请介绍一下自己",
      "created_at": "2026-01-26T10:30:00",
      "updated_at": "2026-01-26T10:35:00",
      "message_count": 4,
      "total_tokens": 256
    }
  ],
  "total": 1
}
```

---

### 2.4 获取会话详情

获取指定会话的详细信息。

**请求**

```http
GET /api/sessions/{session_id}
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | integer | 会话 ID |

**响应示例**

```json
{
  "id": 1,
  "session_name": "你好，请介绍一下自己",
  "created_at": "2026-01-26T10:30:00",
  "updated_at": "2026-01-26T10:35:00",
  "message_count": 4,
  "total_tokens": 256
}
```

**状态码**

- `200`: 成功
- `404`: 会话不存在

---

### 2.5 更新会话名称

修改会话的显示名称。

**请求**

```http
PUT /api/sessions/{session_id}/name
Content-Type: application/json
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | integer | 会话 ID |

**请求体**

```json
{
  "new_name": "关于 AI 的讨论"
}
```

**响应示例**

```json
{
  "success": true,
  "message": "Session name updated"
}
```

---

### 2.6 获取会话消息

获取指定会话的所有消息。

**请求**

```http
GET /api/sessions/{session_id}/messages?limit={limit}
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | integer | 会话 ID |

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| limit | integer | 否 | 限制返回的消息数量（最新的 N 条） |

**响应示例**

```json
{
  "messages": [
    {
      "id": 1,
      "session_id": 1,
      "role": "user",
      "content": "你好，请介绍一下自己",
      "token_count": 12,
      "created_at": "2026-01-26T10:30:00"
    },
    {
      "id": 2,
      "session_id": 1,
      "role": "assistant",
      "content": "你好！我是一个 AI 助手...",
      "token_count": 64,
      "created_at": "2026-01-26T10:30:15"
    }
  ],
  "session_id": 1,
  "total_tokens": 256
}
```

---

### 2.7 添加消息到会话

手动添加消息到指定会话。

**请求**

```http
POST /api/sessions/{session_id}/messages
Content-Type: application/json
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | integer | 会话 ID |

**请求体**

```json
{
  "role": "user",
  "content": "这是一条测试消息"
}
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| role | string | 是 | 角色：`user`、`assistant`、`system` |
| content | string | 是 | 消息内容 |

**响应示例**

```json
{
  "message_id": 3,
  "token_count": 8
}
```

---

### 2.8 清空会话消息

删除指定会话的所有消息（保留会话本身）。

**请求**

```http
DELETE /api/sessions/{session_id}/messages
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | integer | 会话 ID |

**响应示例**

```json
{
  "success": true,
  "message": "Messages cleared"
}
```

---

## 3. 聊天接口

### 3.1 流式聊天

发送消息并接收流式响应（Server-Sent Events）。

**请求**

```http
POST /api/chat
Content-Type: application/json
```

**请求体**

```json
{
  "messages": [
    {
      "role": "user",
      "content": "你好，请介绍一下自己"
    }
  ],
  "session_id": 1,
  "stream": true,
  "temperature": 0.7,
  "repeat_penalty": 1.1,
  "max_tokens": 2048,
  "mode": "llm"
}
```

**参数说明**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| messages | array | 是 | - | 消息列表（通常只包含最新的用户消息） |
| session_id | integer | 是 | - | 会话 ID（必须提供） |
| stream | boolean | 否 | false | 是否使用流式响应 |
| temperature | float | 否 | 0.7 | 温度参数（0.0-2.0） |
| repeat_penalty | float | 否 | 1.1 | 重复惩罚（1.0-2.0） |
| max_tokens | integer | 否 | 2048 | 最大生成 token 数 |
| mode | string | 否 | llm | 模型模式（目前仅支持 `llm`） |

**响应格式（SSE 流）**

```
data: {"choices":[{"delta":{"content":"你好"}}]}

data: {"choices":[{"delta":{"content":"！"}}]}

data: {"choices":[{"delta":{"content":"我是"}}]}

data: [DONE]
```

**响应字段说明**

每个 SSE 事件包含一个 JSON 对象：

```json
{
  "choices": [
    {
      "delta": {
        "content": "生成的文本片段"
      }
    }
  ]
}
```

**错误响应**

```json
{
  "error": "LLM server is not running. Please select a model first."
}
```

**状态码**

- `200`: 成功（流式响应）
- `400`: 请求参数错误（如缺少 session_id）
- `404`: 会话不存在
- `500`: 服务器错误

**重要说明**

1. **必须提供 session_id**：所有聊天都会保存到数据库
2. **自动加载历史**：后端会自动从数据库加载历史消息（在 token 限制内）
3. **自动保存消息**：用户消息和助手响应都会自动保存到数据库
4. **上下文管理**：后端使用 context_size 的一半作为历史消息的最大 token 数
5. **系统提示词**：后端会自动添加系统提示词（从配置读取）

---

## 4. 服务器状态

### 4.1 获取服务器状态

获取指定模式的 llama-server 运行状态。

**请求**

```http
GET /api/server/status?mode={mode}
```

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| mode | string | 否 | llm | 模型模式：`llm`、`embed`、`rerank` |

**响应示例（运行中）**

```json
{
  "status": "running",
  "model_name": "Qwen2.5-0.5B-Instruct-Q4_0",
  "model_path": "/home/user/.cache/zenow/models/llm/Qwen2.5-0.5B-Instruct-Q4_0.gguf",
  "is_running": true,
  "error_message": null
}
```

**响应示例（未启动）**

```json
{
  "status": "not_started",
  "model_name": null,
  "model_path": null,
  "is_running": false,
  "error_message": null
}
```

**响应示例（启动中）**

```json
{
  "status": "starting",
  "model_name": "Qwen2.5-0.5B-Instruct-Q4_0",
  "model_path": "/home/user/.cache/zenow/models/llm/Qwen2.5-0.5B-Instruct-Q4_0.gguf",
  "is_running": false,
  "error_message": null
}
```

**响应示例（错误）**

```json
{
  "status": "error",
  "model_name": "Qwen2.5-0.5B-Instruct-Q4_0",
  "model_path": "/home/user/.cache/zenow/models/llm/Qwen2.5-0.5B-Instruct-Q4_0.gguf",
  "is_running": false,
  "error_message": "Failed to start llama-server: command not found"
}
```

**状态值说明**

- `not_started`: 服务器未启动
- `starting`: 服务器启动中
- `running`: 服务器运行中
- `error`: 服务器启动失败
- `stopped`: 服务器已停止

---

## 5. 数据模型

### 5.1 模型信息 (ModelInfo)

```json
{
  "id": 1,
  "name": "Qwen2.5-0.5B-Instruct-Q4_0",
  "path": "/home/user/.cache/zenow/models/llm/Qwen2.5-0.5B-Instruct-Q4_0.gguf",
  "is_downloaded": true,
  "mode": "llm"
}
```

### 5.2 会话信息 (SessionInfo)

```json
{
  "id": 1,
  "session_name": "你好，请介绍一下自己",
  "created_at": "2026-01-26T10:30:00",
  "updated_at": "2026-01-26T10:35:00",
  "message_count": 4,
  "total_tokens": 256
}
```

### 5.3 消息信息 (MessageInfo)

```json
{
  "id": 1,
  "session_id": 1,
  "role": "user",
  "content": "你好，请介绍一下自己",
  "token_count": 12,
  "created_at": "2026-01-26T10:30:00"
}
```

**角色类型**

- `user`: 用户消息
- `assistant`: 助手消息
- `system`: 系统消息

---

## 6. 错误处理

### 6.1 错误响应格式

所有错误响应都遵循以下格式：

```json
{
  "detail": "错误描述信息"
}
```

### 6.2 常见错误码

| 状态码 | 说明 | 示例 |
|--------|------|------|
| 400 | 请求参数错误 | 缺少必填参数、参数类型错误 |
| 404 | 资源不存在 | 会话不存在、模型不存在 |
| 500 | 服务器内部错误 | 数据库错误、服务器崩溃 |

### 6.3 错误示例

**缺少 session_id**

```json
{
  "detail": "session_id is required. Please create a session first."
}
```

**会话不存在**

```json
{
  "detail": "Session not found"
}
```

**服务器未运行**

```json
{
  "detail": "LLM server is not running. Please select a model first."
}
```

---

## 7. 使用示例

### 7.1 完整聊天流程

```javascript
// 1. 创建会话
const createResponse = await fetch('http://localhost:8050/api/sessions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    first_message: '你好，请介绍一下自己'
  })
});
const { session_id } = await createResponse.json();

// 2. 发送聊天消息（流式）
const chatResponse = await fetch('http://localhost:8050/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    messages: [{ role: 'user', content: '你好，请介绍一下自己' }],
    session_id: session_id,
    stream: true
  })
});

// 3. 处理流式响应
const reader = chatResponse.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = line.slice(6);
      if (data === '[DONE]') break;

      const json = JSON.parse(data);
      const content = json.choices[0]?.delta?.content;
      if (content) {
        console.log(content); // 输出生成的文本
      }
    }
  }
}
```

### 7.2 模型下载与加载

```javascript
// 1. 下载模型
await fetch('http://localhost:8050/api/models/download', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    url: 'https://modelscope.cn/models/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/master/qwen2.5-0.5b-instruct-q4_0.gguf',
    mode: 'llm'
  })
});

// 2. 轮询下载状态
const checkDownload = setInterval(async () => {
  const response = await fetch('http://localhost:8050/api/models/download/status?url=...');
  const { download } = await response.json();

  console.log(`下载进度: ${download.progress}%`);

  if (download.status === 'completed') {
    clearInterval(checkDownload);

    // 3. 加载模型
    await fetch('http://localhost:8050/api/models/load', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model_name: 'Qwen2.5-0.5B-Instruct-Q4_0',
        mode: 'llm'
      })
    });
  }
}, 1000);
```

---

## 8. 注意事项

1. **会话管理**
   - 所有聊天必须关联到会话（session_id 必填）
   - 删除会话会级联删除所有消息
   - 会话名称自动从第一条消息生成（最多 50 字符）

2. **上下文管理**
   - 后端自动管理上下文窗口
   - 历史消息最多占用 context_size 的一半
   - 超出限制的旧消息会被自动截断

3. **模型模式**
   - 三种模式可以同时运行：`llm`、`embed`、`rerank`
   - 每种模式独立配置和管理
   - 聊天功能仅使用 `llm` 模式

4. **流式响应**
   - 使用 Server-Sent Events (SSE) 协议
   - 客户端需要正确处理流式数据
   - 响应结束时会发送 `[DONE]` 标记

5. **参数更新**
   - 修改服务器参数（context_size、threads 等）需要重启服务器
   - 修改客户端参数（temperature、max_tokens 等）立即生效
   - 响应中的 `requires_restart` 字段指示是否需要重启
