"""
Knowledge Base Management API Router

Endpoints for managing knowledge bases and files:
- GET /api/knowledge-bases - List all knowledge bases
- POST /api/knowledge-bases - Create new knowledge base
- GET /api/knowledge-bases/{kb_id} - Get KB details
- PUT /api/knowledge-bases/{kb_id} - Update KB info
- DELETE /api/knowledge-bases/{kb_id} - Delete KB
- POST /api/knowledge-bases/{kb_id}/files - Upload file
- GET /api/knowledge-bases/{kb_id}/files - List KB files
- DELETE /api/knowledge-bases/{kb_id}/files/{file_id} - Delete file
"""

import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Create router
kb_router = APIRouter(prefix="/api/knowledge-bases", tags=["Knowledge Bases"])

# These will be injected from main.py
db_kb = None
minio_client = None


def set_dependencies(db_knowledge_base, minio_client_instance):
    """Set dependencies for this router."""
    global db_kb, minio_client
    db_kb = db_knowledge_base
    minio_client = minio_client_instance


# ============================================================================
# Knowledge Base Management Endpoints
# ============================================================================

@kb_router.get("")
async def list_knowledge_bases():
    """List all knowledge bases."""
    try:
        kbs = await db_kb.list_knowledge_bases()
        return {
            "success": True,
            "knowledge_bases": kbs,
            "count": len(kbs)
        }
    except Exception as e:
        logger.error(f"Failed to list knowledge bases: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@kb_router.post("")
async def create_knowledge_base(
    name: str = Form(...),
    description: str = Form(default=""),
    avatar_url: Optional[str] = Form(default=None)
):
    """Create a new knowledge base."""
    try:
        if not name or not name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Knowledge base name is required"
            )

        kb_id = await db_kb.create_knowledge_base(
            name=name.strip(),
            description=description.strip(),
            avatar_url=avatar_url
        )

        kb = await db_kb.get_knowledge_base(kb_id)
        return {
            "success": True,
            "message": f"Knowledge base '{name}' created successfully",
            "kb_id": kb_id,
            "knowledge_base": kb
        }

    except Exception as e:
        logger.error(f"Failed to create knowledge base: {e}")
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Knowledge base '{name}' already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@kb_router.get("/{kb_id}")
async def get_knowledge_base(kb_id: int):
    """Get knowledge base details."""
    try:
        kb = await db_kb.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base {kb_id} not found"
            )

        return {
            "success": True,
            "knowledge_base": kb
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get knowledge base: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@kb_router.put("/{kb_id}")
async def update_knowledge_base(
    kb_id: int,
    name: Optional[str] = Form(default=None),
    description: Optional[str] = Form(default=None),
    avatar_url: Optional[str] = Form(default=None)
):
    """Update knowledge base information."""
    try:
        # Check if KB exists
        kb = await db_kb.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base {kb_id} not found"
            )

        # Update KB
        success = await db_kb.update_knowledge_base(
            kb_id=kb_id,
            name=name.strip() if name else None,
            description=description.strip() if description else None,
            avatar_url=avatar_url
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update knowledge base"
            )

        updated_kb = await db_kb.get_knowledge_base(kb_id)
        return {
            "success": True,
            "message": "Knowledge base updated successfully",
            "knowledge_base": updated_kb
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update knowledge base: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@kb_router.delete("/{kb_id}")
async def delete_knowledge_base(kb_id: int):
    """Delete knowledge base (cascades to files)."""
    try:
        # Check if KB exists
        kb = await db_kb.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base {kb_id} not found"
            )

        kb_name = kb["name"]

        # Delete all files from MinIO
        if minio_client:
            try:
                prefix = f"{kb_name}/"
                await minio_client.delete_folder(prefix)
            except Exception as e:
                logger.warning(f"Failed to delete files from MinIO: {e}")

        # Delete KB from database (cascades to files)
        success = await db_kb.delete_knowledge_base(kb_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete knowledge base"
            )

        return {
            "success": True,
            "message": f"Knowledge base '{kb_name}' deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete knowledge base: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# File Management Endpoints
# ============================================================================

@kb_router.post("/{kb_id}/files")
async def upload_file(
    kb_id: int,
    file: UploadFile = File(...)
):
    """Upload file to knowledge base."""
    try:
        # Check if KB exists
        kb = await db_kb.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base {kb_id} not found"
            )

        kb_name = kb["name"]

        # Validate file type
        allowed_types = {".md", ".txt", ".pdf"}
        file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""

        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{file_ext}' not allowed. Allowed: {', '.join(allowed_types)}"
            )

        # Read file content
        content = await file.read()
        file_size = len(content)

        # Upload to MinIO
        if not minio_client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="MinIO client not available"
            )

        file_path = f"{kb_name}/{file.filename}"
        await minio_client.upload_file(file_path, content)

        # Add file to database
        file_type = file_ext.lstrip(".")
        file_id = await db_kb.add_file(
            kb_id=kb_id,
            filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type
        )

        file_info = await db_kb.get_file(file_id)
        return {
            "success": True,
            "message": f"File '{file.filename}' uploaded successfully",
            "file_id": file_id,
            "file": file_info
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@kb_router.get("/{kb_id}/files")
async def list_kb_files(kb_id: int):
    """List all files in knowledge base."""
    try:
        # Check if KB exists
        kb = await db_kb.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base {kb_id} not found"
            )

        files = await db_kb.get_kb_files(kb_id)
        return {
            "success": True,
            "files": files,
            "count": len(files)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list KB files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@kb_router.delete("/{kb_id}/files/{file_id}")
async def delete_file(kb_id: int, file_id: int):
    """Delete file from knowledge base."""
    try:
        # Check if KB exists
        kb = await db_kb.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base {kb_id} not found"
            )

        # Get file info
        file_info = await db_kb.get_file(file_id)
        if not file_info or file_info["kb_id"] != kb_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {file_id} not found in KB {kb_id}"
            )

        # Delete from MinIO
        if minio_client:
            try:
                await minio_client.delete_file(file_info["file_path"])
            except Exception as e:
                logger.warning(f"Failed to delete file from MinIO: {e}")

        # Delete from database
        success = await db_kb.delete_file(file_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete file"
            )

        return {
            "success": True,
            "message": f"File '{file_info['filename']}' deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
