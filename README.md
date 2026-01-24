# Zenow Chat

一个基于 Electron + React + FastAPI 的 LLM 聊天应用。

## 技术栈

### 前端
- Electron
- React
- TypeScript
- Vite
- React Router

### 后端
- Python 3.10+
- FastAPI
- uv (Python 包管理)

## 项目结构

```
zenow/
├── frontend/          # Electron + React 前端
│   ├── electron/      # Electron 主进程代码
│   ├── src/          # React 源代码
│   │   ├── pages/    # 页面组件
│   │   ├── App.tsx   # 主应用组件
│   │   └── main.tsx  # React 入口
│   └── package.json
├── backend/          # FastAPI 后端
│   ├── src/
│   │   └── main.py   # FastAPI 应用
│   └── pyproject.toml
└── package.json      # 根项目配置
```

## 安装依赖

### 1. 安装根目录依赖

```bash
npm install
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
cd ..
```

### 3. 安装后端依赖

首先确保安装了 uv:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或者使用 pip
pip install uv
```

然后安装后端依赖:

```bash
cd backend
uv sync
cd ..
```

### 4. 配置后端环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env 文件，添加你的 API keys
```

## 运行应用

### 方式1: 分别启动前后端

```bash
# 启动后端 (在一个终端)
npm run back

# 启动前端 (在另一个终端)
npm run front
```

### 方式2: 同时启动前后端

```bash
npm run all
```

## 功能特性 (Version 0)

### 聊天页面
- 左上角显示当前使用的模型
- 消息输入框,支持发送聊天消息
- 消息历史记录显示
- 实时与 LLM 对话

### 设置页面
- 查看当前使用的模型
- 切换不同的 AI 模型
- 支持多种模型选择:
  - GPT-3.5 Turbo
  - GPT-4
  - GPT-4 Turbo
  - Claude 3 Opus
  - Claude 3 Sonnet

## API 端点

后端 API 运行在 `http://localhost:8000`

- `GET /api/models` - 获取可用模型列表
- `GET /api/models/current` - 获取当前模型
- `POST /api/models/current` - 设置当前模型
- `POST /api/chat` - 发送聊天消息

## 开发说明

### 前端开发
- 使用 Vite 进行快速开发和热重载
- 使用 TypeScript 确保类型安全
- 使用 React Router 进行页面路由

### 后端开发
- 使用 FastAPI 提供 RESTful API
- 支持 CORS 以允许前端访问
- 使用 uv 管理 Python 依赖

## 注意事项

1. 确保后端服务器在 8000 端口运行
2. 前端开发服务器默认在 5173 端口
3. 需要配置有效的 API keys 才能使用实际的 LLM 功能
4. 当前版本使用 mock 响应,需要集成实际的 LLM API

## 后续计划

- [ ] 集成实际的 OpenAI/Anthropic API
- [ ] 添加聊天历史持久化
- [ ] 支持多会话管理
- [ ] 添加流式响应
- [ ] 优化 UI/UX
- [ ] 添加更多模型支持
