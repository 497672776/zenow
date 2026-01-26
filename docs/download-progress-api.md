# 模型下载进度 API 使用指南

## API 端点

### 1. 启动下载

**端点:** `POST /api/models/download`

**请求体:**
```json
{
  "url": "https://example.com/model.gguf",
  "filename": "model.gguf",  // 可选
  "mode": "llm"              // 可选: "llm", "embed", "rerank"
}
```

**响应:**
```json
{
  "success": true,
  "url": "https://example.com/model.gguf",
  "mode": "llm",
  "message": "Download started"
}
```

### 2. 查询下载进度

**端点:** `GET /api/models/download/status`

**查询参数:**
- `url` (可选): 指定 URL 的下载状态。如果不提供，返回所有下载状态

**响应 (单个下载):**
```json
{
  "success": true,
  "download": {
    "url": "https://example.com/model.gguf",
    "filename": "model.gguf",
    "status": "downloading",  // "downloading", "completed", "failed"
    "downloaded": 104857600,  // 已下载字节数
    "total": 524288000,       // 总字节数
    "progress": 20.0          // 进度百分比
  }
}
```

**响应 (所有下载):**
```json
{
  "success": true,
  "downloads": {
    "https://example.com/model1.gguf": {
      "url": "https://example.com/model1.gguf",
      "filename": "model1.gguf",
      "status": "downloading",
      "downloaded": 104857600,
      "total": 524288000,
      "progress": 20.0
    },
    "https://example.com/model2.gguf": {
      "url": "https://example.com/model2.gguf",
      "filename": "model2.gguf",
      "status": "completed",
      "downloaded": 314572800,
      "total": 314572800,
      "progress": 100.0
    }
  }
}
```

## 前端使用示例

### React/TypeScript 示例

```typescript
// 下载进度组件
import React, { useState, useEffect } from 'react';

interface DownloadProgress {
  url: string;
  filename: string;
  status: 'downloading' | 'completed' | 'failed';
  downloaded: number;
  total: number;
  progress: number;
  error?: string;
}

export const ModelDownloader: React.FC<{ url: string; mode: string }> = ({ url, mode }) => {
  const [progress, setProgress] = useState<DownloadProgress | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);

  // 启动下载
  const startDownload = async () => {
    try {
      const response = await fetch('http://localhost:8050/api/models/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, mode })
      });

      const data = await response.json();
      if (data.success) {
        setIsDownloading(true);
      }
    } catch (error) {
      console.error('Failed to start download:', error);
    }
  };

  // 轮询下载进度
  useEffect(() => {
    if (!isDownloading) return;

    const interval = setInterval(async () => {
      try {
        const response = await fetch(
          `http://localhost:8050/api/models/download/status?url=${encodeURIComponent(url)}`
        );
        const data = await response.json();

        if (data.success && data.download) {
          setProgress(data.download);

          // 下载完成或失败时停止轮询
          if (data.download.status === 'completed' || data.download.status === 'failed') {
            setIsDownloading(false);
          }
        }
      } catch (error) {
        console.error('Failed to fetch progress:', error);
      }
    }, 1000); // 每秒查询一次

    return () => clearInterval(interval);
  }, [isDownloading, url]);

  return (
    <div>
      {!isDownloading && !progress && (
        <button onClick={startDownload}>开始下载</button>
      )}

      {progress && (
        <div>
          <div>文件名: {progress.filename}</div>
          <div>状态: {progress.status}</div>
          <div>进度: {progress.progress.toFixed(2)}%</div>
          <div>
            已下载: {(progress.downloaded / 1024 / 1024).toFixed(2)} MB /
            {(progress.total / 1024 / 1024).toFixed(2)} MB
          </div>

          {/* 进度条 */}
          <div style={{ width: '100%', height: '20px', backgroundColor: '#eee' }}>
            <div
              style={{
                width: `${progress.progress}%`,
                height: '100%',
                backgroundColor: progress.status === 'completed' ? '#4caf50' : '#2196f3',
                transition: 'width 0.3s'
              }}
            />
          </div>

          {progress.status === 'failed' && (
            <div style={{ color: 'red' }}>错误: {progress.error}</div>
          )}
        </div>
      )}
    </div>
  );
};
```

### 简单的 JavaScript 示例

```javascript
// 启动下载
async function startDownload(url, mode = 'llm') {
  const response = await fetch('http://localhost:8050/api/models/download', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, mode })
  });
  return response.json();
}

// 查询下载进度
async function getDownloadProgress(url) {
  const response = await fetch(
    `http://localhost:8050/api/models/download/status?url=${encodeURIComponent(url)}`
  );
  return response.json();
}

// 轮询下载进度
async function pollDownloadProgress(url, onProgress, onComplete) {
  const interval = setInterval(async () => {
    const data = await getDownloadProgress(url);

    if (data.success && data.download) {
      onProgress(data.download);

      if (data.download.status === 'completed') {
        clearInterval(interval);
        onComplete(data.download);
      } else if (data.download.status === 'failed') {
        clearInterval(interval);
        console.error('Download failed:', data.download.error);
      }
    }
  }, 1000);

  return interval;
}

// 使用示例
const url = 'https://example.com/model.gguf';

startDownload(url, 'llm').then(() => {
  console.log('Download started');

  pollDownloadProgress(
    url,
    (progress) => {
      console.log(`Progress: ${progress.progress.toFixed(2)}%`);
    },
    (result) => {
      console.log('Download completed!', result);
    }
  );
});
```

## 注意事项

1. **轮询频率**: 建议每 1-2 秒查询一次进度，避免过于频繁的请求
2. **错误处理**: 下载失败时，`status` 为 `"failed"`，`error` 字段包含错误信息
3. **并发下载**: 系统支持同时下载多个模型，使用 URL 作为唯一标识
4. **下载完成**: 当 `status` 为 `"completed"` 时，可以停止轮询
5. **文件已存在**: 如果文件已存在，下载会立即完成（progress = 100%）

## 完整工作流程

```
1. 用户点击"下载模型"
   ↓
2. 前端调用 POST /api/models/download
   ↓
3. 后端启动异步下载任务
   ↓
4. 前端开始轮询 GET /api/models/download/status
   ↓
5. 显示进度条和下载信息
   ↓
6. 下载完成后停止轮询
   ↓
7. 更新 UI 显示"下载完成"
```

## 测试

运行测试脚本：
```bash
cd backend
python3 test_download_progress.py
```

这将测试完整的下载进度功能。
