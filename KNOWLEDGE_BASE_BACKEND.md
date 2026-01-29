# 知识库管理系统 - 后端实现总结

## 架构概览

知识库管理系统由以下三个核心模块组成：

### 1. 数据库层 (SQLiteKnowledgeBase)
**文件**: `backend/spacemit_llm/comon/sqlite/sqlit_kb.py`

**数据库表结构**:

#### knowledge_bases 表
```sql
CREATE TABLE knowledge_bases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,              -- 知识库名称（唯一）
    description TEXT,                       -- 知识库描述
    avatar_url TEXT,                        -- 头像URL
    doc_count INTEGER DEFAULT 0,            -- 文档数量（自动计算）
    total_size INTEGER DEFAULT 0,           -- 总大小（自动计算）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### kb_files 表
```sql
CREATE TABLE kb_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kb_id INTEGER NOT NULL,                 -- 知识库ID（外键）
    filename TEXT NOT NULL,                 -- 原始文件名
    file_path TEXT NOT NULL,                -- MinIO中的路径
    file_size INTEGER NOT NULL,             -- 文件大小（字节）
    file_type TEXT NOT NULL,                -- 文件类型 (md/txt/pdf)
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    UNIQUE(kb_id, filename)                 -- 同KB内文件名唯一
)
```

**关键特性**:
- 级联删除：删除知识库时自动删除所有关联文件
- 自动统计：doc_count和total_size自动计算
- 文件覆盖：同名文件上传时自动覆盖并更新时间戳
- 时间戳追踪：记录创建和更新时间

### 2. 文件存储层 (MinIO)
**文件**: `backend/spacemit_llm/comon/minio.py`

**功能**:
- MinioServer: 管理MinIO服务的启动/停止/健康检查
- MinioClient: 提供文件上传/下载/删除/列表操作

**存储结构**:
```
bucket: rag-documents
├── kb-name-1/
│   ├── document1.pdf
│   ├── document2.md
│   └── document3.txt
├── kb-name-2/
│   ├── file1.pdf
│   └── file2.txt
```

**支持的文件类型**: `.md`, `.txt`, `.pdf`

### 3. API层 (FastAPI 路由)
**文件**: `backend/routers/knowledge_base.py`

## API 端点

### 知识库管理

#### 获取知识库列表
```
GET /api/knowledge-bases
```
**响应**:
```json
{
  "success": true,
  "knowledge_bases": [
    {
      "id": 1,
      "name": "My KB",
      "description": "Description",
      "avatar_url": null,
      "doc_count": 2,
      "total_size": 102400,
      "created_at": "2024-01-29T10:00:00",
      "updated_at": "2024-01-29T10:30:00"
    }
  ],
  "count": 1
}
```

#### 创建知识库
```
POST /api/knowledge-bases
Content-Type: multipart/form-data

name: "My Knowledge Base"
description: "Optional description"
avatar_url: "https://example.com/avatar.png"  (optional)
```

**响应**:
```json
{
  "success": true,
  "message": "Knowledge base 'My Knowledge Base' created successfully",
  "kb_id": 1,
  "knowledge_base": { ... }
}
```

#### 获取知识库详情
```
GET /api/knowledge-bases/{kb_id}
```

#### 更新知识库
```
PUT /api/knowledge-bases/{kb_id}
Content-Type: multipart/form-data

name: "Updated Name"  (optional)
description: "Updated description"  (optional)
avatar_url: "https://example.com/new-avatar.png"  (optional)
```

#### 删除知识库
```
DELETE /api/knowledge-bases/{kb_id}
```
**注意**: 自动删除MinIO中的所有文件和数据库记录

### 文件管理

#### 上传文件
```
POST /api/knowledge-bases/{kb_id}/files
Content-Type: multipart/form-data

file: <binary file content>
```

**支持的文件类型**: `.md`, `.txt`, `.pdf`

**响应**:
```json
{
  "success": true,
  "message": "File 'document.pdf' uploaded successfully",
  "file_id": 1,
  "file": {
    "id": 1,
    "kb_id": 1,
    "filename": "document.pdf",
    "file_path": "My KB/document.pdf",
    "file_size": 102400,
    "file_type": "pdf",
    "uploaded_at": "2024-01-29T10:00:00",
    "updated_at": "2024-01-29T10:00:00"
  }
}
```

#### 获取知识库中的文件列表
```
GET /api/knowledge-bases/{kb_id}/files
```

**响应**:
```json
{
  "success": true,
  "files": [
    {
      "id": 1,
      "kb_id": 1,
      "filename": "document.pdf",
      "file_path": "My KB/document.pdf",
      "file_size": 102400,
      "file_type": "pdf",
      "uploaded_at": "2024-01-29T10:00:00",
      "updated_at": "2024-01-29T10:00:00"
    }
  ],
  "count": 1
}
```

#### 删除文件
```
DELETE /api/knowledge-bases/{kb_id}/files/{file_id}
```

**响应**:
```json
{
  "success": true,
  "message": "File 'document.pdf' deleted successfully"
}
```

## 启动流程

### 1. 后端启动
```bash
cd backend
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8050
```

### 2. 启动事件 (startup_event)
1. 启动MinIO服务
   - 检查MinIO二进制文件
   - 创建数据目录
   - 启动MinIO进程
   - 等待健康检查通过

2. 初始化数据库
   - 创建knowledge_bases表
   - 创建kb_files表

3. 启动LLM模型服务器

### 3. 关闭事件 (shutdown_event)
1. 停止所有llama-server进程
2. 停止MinIO服务
3. 清理端口文件

## 文件覆盖逻辑

当上传同名文件时：
1. 检查是否存在相同kb_id和filename的记录
2. 如果存在：
   - 更新file_path（覆盖MinIO中的文件）
   - 更新file_size
   - 更新updated_at时间戳
3. 如果不存在：
   - 创建新记录

## 级联删除逻辑

删除知识库时：
1. 获取知识库中的所有文件
2. 从MinIO删除所有文件（按前缀）
3. 从数据库删除知识库记录
4. 自动删除所有关联的文件记录（外键级联）

## 错误处理

所有API端点都返回标准的HTTP状态码：
- `200 OK`: 成功
- `400 Bad Request`: 请求参数错误
- `404 Not Found`: 资源不存在
- `409 Conflict`: 冲突（如知识库名称已存在）
- `500 Internal Server Error`: 服务器错误

## 配置

### MinIO配置
- 端点: `localhost:9000`
- 控制台: `localhost:9001`
- 访问密钥: `minioadmin`
- 密钥: `minioadmin`
- 数据目录: `~/.cache/rag_chat/documents`
- Bucket: `rag-documents`

### 数据库配置
- 路径: `~/.cache/zenow/data/db/knowledge_base.db`

## 前端集成

前端通过以下API与后端通信：

1. **获取知识库列表**: `GET /api/knowledge-bases`
2. **创建知识库**: `POST /api/knowledge-bases`
3. **上传文件**: `POST /api/knowledge-bases/{kb_id}/files`
4. **获取文件列表**: `GET /api/knowledge-bases/{kb_id}/files`
5. **删除知识库**: `DELETE /api/knowledge-bases/{kb_id}`
6. **删除文件**: `DELETE /api/knowledge-bases/{kb_id}/files/{file_id}`

## 下一步

- [ ] 实现文件内容解析（提取文本）
- [ ] 实现向量化和嵌入存储
- [ ] 实现RAG检索功能
- [ ] 添加文件预览功能
- [ ] 实现文件搜索功能
