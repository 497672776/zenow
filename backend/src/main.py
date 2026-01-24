# -*- coding: utf-8 -*-
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
from dotenv import load_dotenv

from src.model.llm import LLMServer, LLMClient
from src.comon.sqlite.sqlite_config import SQLiteConfig
from src.config import (
    DB_CONFIG_PATH,
    LLM_CLIENT_BASE_URL,
    LLM_CLIENT_TEMPERATURE,
    LLM_CLIENT_REPEAT_PENALTY,
    LLM_CLIENT_MAX_TOKENS
)

# Load environment variables
load_dotenv()

app = FastAPI(title="Zenow LLM Chat API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
db_config = SQLiteConfig(DB_CONFIG_PATH)
llm_server = LLMServer()
llm_client = LLMClient(
    base_url=LLM_CLIENT_BASE_URL,
    temperature=LLM_CLIENT_TEMPERATURE,
    repeat_penalty=LLM_CLIENT_REPEAT_PENALTY,
    max_tokens=LLM_CLIENT_MAX_TOKENS
)

# Models
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    stream: Optional[bool] = False
    temperature: Optional[float] = None
    repeat_penalty: Optional[float] = None
    max_tokens: Optional[int] = None

class ChatResponse(BaseModel):
    message: Message
    model: str

class ModelInfo(BaseModel):
    id: int
    name: str
    path: str
    status: str

class ModelListResponse(BaseModel):
    models: List[ModelInfo]
    current_model: Optional[ModelInfo] = None

class AddModelRequest(BaseModel):
    name: str
    path: str

class ServerStatusResponse(BaseModel):
    status: str
    model_name: Optional[str] = None
    model_path: Optional[str] = None
    is_running: bool
    error_message: Optional[str] = None


@app.get("/")
async def root():
    return {"message": "Zenow LLM Chat API"}


@app.get("/api/models", response_model=ModelListResponse)
async def get_models():
    """Get list of available models and current model"""
    try:
        models = db_config.get_all_models()
        current = db_config.get_current_model()

        model_list = [
            ModelInfo(
                id=m["id"],
                name=m["model_name"],
                path=m["model_path"],
                status=m["status"]
            )
            for m in models
        ]

        current_model_info = None
        if current:
            current_model_info = ModelInfo(
                id=current["id"],
                name=current["model_name"],
                path=current["model_path"],
                status=current["status"]
            )

        return ModelListResponse(
            models=model_list,
            current_model=current_model_info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/models/add")
async def add_model(request: AddModelRequest):
    """Add a new model to the database"""
    try:
        model_id = db_config.add_model(request.name, request.path)
        return {"success": True, "model_id": model_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/models/current")
async def set_current_model(model_id: int):
    """Set the current model"""
    try:
        success = db_config.set_current_model(model_id)
        if success:
            return {"success": True, "model_id": model_id}
        else:
            raise HTTPException(status_code=404, detail="Model not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/current")
async def get_current_model():
    """Get the current model"""
    try:
        current = db_config.get_current_model()
        if current:
            return ModelInfo(
                id=current["id"],
                name=current["model_name"],
                path=current["model_path"],
                status=current["status"]
            )
        else:
            return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/server/start")
async def start_server():
    """Start the LLM server with current model"""
    try:
        current_model = db_config.get_current_model()
        if not current_model:
            raise HTTPException(status_code=400, detail="No current model set")

        success = llm_server.start_server(
            model_path=current_model["model_path"],
            model_name=current_model["model_name"]
        )

        if success:
            return {"success": True, "model": current_model["model_name"]}
        else:
            raise HTTPException(status_code=500, detail="Failed to start server")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/server/stop")
async def stop_server():
    """Stop the LLM server"""
    try:
        success = llm_server.stop_server()
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/server/status", response_model=ServerStatusResponse)
async def get_server_status():
    """Get the LLM server status"""
    try:
        status = llm_server.get_status()
        return ServerStatusResponse(**status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/server/switch")
async def switch_model(model_id: int):
    """Switch to a different model"""
    try:
        # Get model from database
        models = db_config.get_all_models()
        target_model = None
        for m in models:
            if m["id"] == model_id:
                target_model = m
                break

        if not target_model:
            raise HTTPException(status_code=404, detail="Model not found")

        # Switch model
        success = llm_server.switch_model(
            model_path=target_model["model_path"],
            model_name=target_model["model_name"]
        )

        if success:
            db_config.set_current_model(model_id)
            return {"success": True, "model": target_model["model_name"]}
        else:
            raise HTTPException(status_code=500, detail="Failed to switch model")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Send a chat message and get a response"""
    try:
        # Check if server is running
        status = llm_server.get_status()
        if not status["is_running"]:
            raise HTTPException(status_code=400, detail="LLM server is not running")

        # Convert messages to dict format
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        # Handle streaming response
        if request.stream:
            async def generate():
                try:
                    for chunk in llm_client.chat_completion(
                        messages=messages,
                        stream=True,
                        temperature=request.temperature,
                        repeat_penalty=request.repeat_penalty,
                        max_tokens=request.max_tokens
                    ):
                        # Send SSE formatted data
                        yield f"data: {json.dumps(chunk)}\n\n"

                    # Send done signal
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    error_data = {"error": str(e)}
                    yield f"data: {json.dumps(error_data)}\n\n"

            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            # Non-streaming response
            response = llm_client.chat_completion(
                messages=messages,
                stream=False,
                temperature=request.temperature,
                repeat_penalty=request.repeat_penalty,
                max_tokens=request.max_tokens
            )

            return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
