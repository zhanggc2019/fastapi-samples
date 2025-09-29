import os
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from app.api.deps import CurrentUser, SessionDep
from app.models import FileUploadResponse
from core.path_config import UPLOAD_DIR

router = APIRouter()


@router.post("/files/upload", response_model=FileUploadResponse)
async def upload_file(
    *, _db: SessionDep, _current_user: CurrentUser, file: UploadFile = File(...)
) -> Any:
    """
    上传文件
    """
    if file.content_type not in {"image/jpeg", "image/png"}:
        return JSONResponse(
            status_code=400,
            content={"error": "File type should be JPEG or PNG"},
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
            if len(content) > 5 * 1024 * 1024:
                return JSONResponse(
                    status_code=400,
                    content={"error": "File size should be less than 5MB"},
                )
            buffer.write(content)

        # 构建文件URL
        file_url = f"/static/upload/{unique_filename}"

        response = FileUploadResponse(
            url=file_url,
            pathname=unique_filename,
            contentType=file.content_type or "application/octet-stream",
            size=len(content),
            uploadedAt=datetime.now(UTC),
        )
        return response

    except Exception as exc:  # noqa: BLE001 - 记录异常即可
        return JSONResponse(
            status_code=500,
            content={"error": f"Upload failed: {exc}"},
        )
