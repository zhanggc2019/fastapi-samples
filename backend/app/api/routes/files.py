import os
import uuid
from typing import Any
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, SessionDep
from app.models import FileUploadResponse
from core.path_config import UPLOAD_DIR

router = APIRouter()


@router.post("/files/upload", response_model=FileUploadResponse)
async def upload_file(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    file: UploadFile = File(...)
) -> Any:
    """
    上传文件
    """
    # 验证文件类型
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type should be JPEG or PNG"
        )
    
    # 验证文件大小 (5MB)
    if file.size and file.size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size should be less than 5MB"
        )
    
    try:
        # 生成唯一文件名
        file_extension = os.path.splitext(file.filename or "")[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # 确保上传目录存在
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 构建文件URL
        file_url = f"/static/upload/{unique_filename}"
        
        return FileUploadResponse(
            success=True,
            filename=unique_filename,
            url=file_url,
            size=len(content),
            contentType=file.content_type or "application/octet-stream"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )
