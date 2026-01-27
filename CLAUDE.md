# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Zenow is an LLM chat application built with Electron + React + FastAPI. It provides a desktop interface for chatting with local LLM models using GGUF format files via llama-server.

**Tech Stack:**
- Frontend: Electron, React, TypeScript, Vite, React Router
- Backend: Python 3.12, FastAPI, uv (package manager)
- LLM: llama-server with GGUF models

## Development Commands

### Installation

```bash
# Root dependencies
npm install

# Frontend dependencies
cd frontend && npm install && cd ..

# Backend dependencies (requires uv)
cd backend && uv sync && cd ..
```

### Running the Application

```bash
# Run both frontend and backend concurrently
npm run all

# Run separately
npm run front  # Frontend only (Vite dev server on port 5173)
npm run back   # Backend only (FastAPI on port 8050)
```

### Backend Commands

```bash
cd backend
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8050
```

### Frontend Commands

```bash
cd frontend
npm run dev              # Vite dev server
npm run build            # Build for production
npm run electron:dev     # Run Electron in dev mode
npm run electron:build   # Build Electron app
```

## Architecture

### Backend Architecture

**Core Components:**

1. **Model Server Manager** (`backend/src/model/server_manager.py`)
   - `ModelServerManager`: Manages multiple concurrent llama-server processes
   - Supports three model modes: LLM (port 8051), Embed (port 8052), Rerank (port 8053)
   - Each mode can run one llama-server process simultaneously
   - Provides unified interface for server/client access across all modes

2. **LLM Server & Client** (`backend/src/model/llm.py`)
   - `LLMServer`: Manages llama-server subprocess for chat/completion
   - `LLMClient`: Async HTTP client for streaming chat completions
   - Model states: `not_started`, `starting`, `running`, `error`, `stopped`
   - Configurable: temperature, repeat_penalty, max_tokens, context_size, threads, gpu_layers

3. **Embed Server & Client** (`backend/src/model/embed.py`)
   - `EmbedServer`: Manages llama-server with `--embedding` flag for text embeddings
   - `EmbedClient`: Async client for generating text embeddings
   - Supports batch embedding, normalization, and truncation
   - Default context size: 8192 (smaller than LLM)

4. **Rerank Server & Client** (`backend/src/model/rerank.py`)
   - `RerankServer`: Manages llama-server with `--reranking` flag for document reranking
   - `RerankClient`: Async client for reranking documents by relevance
   - Returns top-N results with relevance scores
   - Default context size: 8192

5. **Model Management** (`backend/src/model/download.py`)
   - `ModelDownloader`: Downloads GGUF models from URLs
   - Tracks download progress and status
   - Stores models in mode-specific directories: `~/.cache/zenow/models/{llm,embed,rerank}/`

6. **Pipelines** (`backend/src/pipeline/`)
   - `ModelSelectionPipeline`: Handles model selection workflow (download → stop old server → start new server)
   - `BackendStartupHandler`: Initializes database and starts last-used model on startup
   - `BackendExitHandler`: Cleans up all llama-server processes on backend shutdown
   - `ModelParameterChangePipeline`: Updates model parameters and restarts server if needed

7. **Database** (`backend/src/comon/sqlite/`)
   - `SQLiteConfig`: Stores configuration per mode (current model, parameters)
     - Located at `~/.cache/zenow/data/db/config.db`
     - Tracks `is_downloaded` status for each model
     - Persists settings across backend restarts
   - `SQLiteSession`: Manages chat sessions and message history
     - Located at `~/.cache/zenow/data/db/session.db`
     - Tables: `sessions` (id, session_name, created_at, updated_at, message_count, total_tokens)
     - Tables: `messages` (id, session_id, role, content, token_count, created_at)
     - Supports cascading deletes (deleting session removes all messages)
     - Auto-generates session names from first user message (max 50 chars)

8. **Utilities** (`backend/src/utils/`)
   - `token_estimator.py`: Estimates token count for messages (4 chars ≈ 1 token)
   - Used for context window management and session token tracking

9. **Configuration** (`backend/src/config.py`)
   - Default paths: `~/.cache/zenow/` (base), `~/.cache/zenow/models/{llm,embed,rerank}/` (models)
   - Default server ports: LLM=8051, Embed=8052, Rerank=8053
   - Default API server: `0.0.0.0:8050`
   - Default model download URLs per mode in `DEFAULT_MODEL_DOWNLOAD_URLS`

**API Endpoints** (FastAPI on port 8050):

*Core Model Management (6 endpoints):*
- `GET /api/models/current?mode={llm|embed|rerank}` - Get current model for mode
- `GET /api/models/list?mode={llm|embed|rerank}` - List models for specific mode
- `POST /api/models/load` - Load/switch model (with mode parameter)
- `POST /api/models/download` - Download model from URL (with mode parameter)
- `GET /api/models/download/status?url={url}` - Check download progress
- `GET /api/models/get_param?mode={llm|embed|rerank}` - Get parameters for mode
- `POST /api/models/update_param?mode={llm|embed|rerank}` - Update parameters (with mode parameter)

*Session Management:*
- `POST /api/sessions` - Create new session with first message
- `GET /api/sessions?limit={limit}&offset={offset}` - Get session list (sorted by updated_at desc)
- `GET /api/sessions/{session_id}` - Get session details
- `PUT /api/sessions/{session_id}/name` - Update session name
- `DELETE /api/sessions/{session_id}` - Delete session (cascades to messages)
- `GET /api/sessions/{session_id}/messages?limit={limit}` - Get messages for session
- `POST /api/sessions/{session_id}/messages` - Add message to session
- `DELETE /api/sessions/{session_id}/messages` - Clear all messages in session

*Chat & Auxiliary:*
- `POST /api/chat` - Stream chat completions (requires session_id, saves to database)
- `GET /api/server/status?mode={llm|embed|rerank}` - Get server status for mode
- `GET /api/downloads/default-urls` - Get default download URLs for all modes

### Frontend Architecture

**Core Components:**

1. **Electron Main Process** (`frontend/electron/main.ts`)
   - Frameless window with custom title bar
   - IPC handlers for window controls (minimize, maximize, close)
   - File dialog for selecting GGUF models
   - Reads backend port from `~/.config/zenow/backend.port`

2. **Pages** (`frontend/src/pages/`)
   - `ChatPage.tsx`: Main chat interface with streaming responses (20ms throttled rendering)
     - Two modes: New chat (creates session on first message) or existing session (loads history)
     - Requires session_id for all chat operations
     - Automatically loads message history from database
     - Implements context window management (uses half of context_size for history)
   - `SettingsPage.tsx`: Model selection, download, parameter configuration
   - `HistoryPage.tsx`: Chat history (placeholder)
   - `KnowledgeBasePage.tsx`: Knowledge base management (placeholder)

3. **Components** (`frontend/src/components/`)
   - `TitleBar.tsx`: Custom title bar with window controls and page title
   - `ModelDropdown.tsx`: Model selection dropdown with status indicators
   - `ModelSection.tsx`: Reusable component for managing models by mode (LLM/Embed/Rerank)
   - `Sidebar.tsx`: Navigation sidebar with session list
   - `SessionList.tsx`: Displays session history grouped by time (Today/7 Days/Older)
     - Supports session rename, delete with confirmation modal
     - Implements refresh trigger mechanism for real-time updates
     - Cascading delete: removes session and all associated messages

4. **Backend Communication** (`frontend/src/utils/backendPort.ts`)
   - Reads backend port from file written by backend on startup
   - Port file contains: `<port>\n<pid>\n`

**UI Features:**
- Custom frameless window with rounded corners
- Split title bar (left: gray sidebar color, right: white with controls)
- Sidebar navigation: New Chat, Knowledge Base, History, Settings
- Model status indicators: red (not started), yellow (starting), green (running)
- Streaming chat with 20ms throttled rendering

### Inter-Process Communication

1. **Backend Port Discovery:**
   - Backend writes port to `~/.config/zenow/backend.port` on startup
   - Frontend reads this file via Electron IPC to discover backend URL

2. **Model Selection Flow (Multi-Mode):**
   - User selects model in Settings for specific mode (LLM/Embed/Rerank)
   - Frontend calls `/api/models/load` with mode parameter
   - Backend pipeline: download if needed → stop old server for that mode → start new server
   - Frontend polls `/api/server/status?mode={mode}` to show progress
   - Multiple modes can run simultaneously on different ports

3. **Chat Flow:**
   - User creates new session or selects existing session
   - Frontend sends messages to `/api/chat` with session_id (uses LLM mode)
   - Backend loads message history from database (within token limit)
   - Backend constructs prompt: [system] + [history] + [new_message]
   - Backend streams SSE events from llama-server
   - Frontend renders with 20ms throttling for smooth UX
   - Backend saves both user and assistant messages to database
   - Session list updates via refresh trigger mechanism

4. **Multi-Server Architecture:**
   - Three llama-server processes can run concurrently (one per mode)
   - LLM server: Chat completions on port 8051
   - Embed server: Text embeddings on port 8052 with `--embedding` flag
   - Rerank server: Document reranking on port 8053 with `--reranking` flag
   - Each server is independently managed and can be started/stopped without affecting others

## Important Constraints

1. **File Size Limit**: No file should exceed 1000 lines
2. **Python Version**: Requires Python 3.12.11 (specified in pyproject.toml)
3. **Model Format**: Only GGUF format models are supported
4. **llama-server**: Must be available in PATH (not bundled with app)

## Configuration Files

- `backend/.env`: API keys and environment variables (not in repo)
- `backend/src/config.py`: Default configuration values, model download URLs per mode, system prompt
- `~/.cache/zenow/data/db/config.db`: Runtime configuration database (per-mode settings)
- `~/.cache/zenow/data/db/session.db`: Session and message history database
- `~/.config/zenow/backend.port`: Backend port file for frontend discovery
- `~/.cache/zenow/models/llm/`: LLM model storage directory
- `~/.cache/zenow/models/embed/`: Embed model storage directory
- `~/.cache/zenow/models/rerank/`: Rerank model storage directory

## Utility Scripts

### Cache Cleaning Tool (`scripts/clean_cache.sh`)

Interactive script for managing Zenow cache and configuration:

```bash
# Run the cache cleaning tool
./scripts/clean_cache.sh
```

**Features:**
- View cache status and disk usage
- Clean models by mode (LLM/Embed/Rerank) or all at once
- Clean database (resets configuration)
- Clean configuration files
- Complete cleanup option (requires 'YES' confirmation)

**Use cases:**
- Free disk space by removing unused models
- Reset configuration when troubleshooting
- Clean install by removing all data

## Testing

Backend tests are in `backend/tests/`. Example test uses models from `~/Downloads/models/`.

## Common Workflows

### Creating and Managing Sessions
1. User clicks "New Chat" in sidebar
2. User sends first message → Frontend calls `/api/sessions` with first_message
3. Backend creates session, auto-generates name from message (max 50 chars)
4. Backend returns session_id and session_name
5. Frontend switches to this session and sends chat message
6. User can rename session via three-dot menu → calls `/api/sessions/{id}/name`
7. User can delete session via three-dot menu → shows confirmation modal → calls `/api/sessions/{id}` DELETE
8. Deletion cascades to all messages in that session

### Adding a New Model
1. User provides GGUF file path or download URL in Settings
2. User selects mode (LLM/Embed/Rerank) in the appropriate section
3. If URL: ModelDownloader downloads to `~/.cache/zenow/models/{mode}/`
4. Model added to database via SQLiteConfig with mode association
5. User selects model → ModelSelectionPipeline starts llama-server for that mode

### Changing Model Parameters
1. User modifies parameters in Settings (context_size, threads, temperature, etc.)
2. Frontend calls `/api/models/update_param?mode={mode}` with new values
3. ModelParameterChangePipeline updates database and restarts llama-server if server params changed
4. Only the affected mode's server is restarted

### Backend Startup
1. BackendStartupHandler reads last-used models from database for all modes
2. For each mode, if model exists and is downloaded, starts corresponding llama-server
3. Writes port file for frontend discovery
4. All three servers can auto-start if previously configured

### Backend Shutdown
1. BackendExitHandler registered with atexit and signal handlers
2. Stops all llama-server subprocesses gracefully (LLM, Embed, Rerank)
3. Cleans up port file

### Running Multiple Model Modes
1. User can configure and run LLM, Embed, and Rerank models simultaneously
2. Each mode operates on its own port with independent configuration
3. Settings page shows separate sections for each mode with status indicators
4. Models can be switched per mode without affecting other running modes

### Chat with Context Management
1. User sends message in existing session
2. Backend retrieves context_size parameter from database
3. Backend loads message history within token limit (max = context_size / 2)
4. Backend estimates tokens for system prompt and subtracts from available history tokens
5. Backend constructs full prompt and sends to llama-server
6. Streaming response is saved to database with estimated token count
7. Session's updated_at timestamp and token count are automatically updated
