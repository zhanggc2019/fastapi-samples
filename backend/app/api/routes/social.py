import hashlib
import os
import secrets
import time
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.api.deps import SessionDep
from app.models import XhsShareRequest, XhsShareResponse

router = APIRouter()


@router.post("/xhs/share-config", response_model=XhsShareResponse)
async def create_xhs_share_config(
    *, _db: SessionDep, share_request: XhsShareRequest
) -> Any:
    """
    生成小红书分享配置
    """
    if share_request.type == "video":
        if not share_request.video or not share_request.cover:
            return JSONResponse(
                status_code=400,
                content={"message": "video url and cover are required for video posts"},
            )

    if share_request.type == "normal":
        if not share_request.images or len(share_request.images) == 0:
            return JSONResponse(
                status_code=400,
                content={"message": "at least one image is required for normal posts"},
            )

    app_key = os.getenv("XHS_APP_KEY")
    access_token = os.getenv("XHS_ACCESS_TOKEN")

    if not app_key or not access_token:
        return JSONResponse(
            status_code=500,
            content={
                "message": "Missing XHS_APP_KEY or XHS_ACCESS_TOKEN environment variables.",
            },
        )

    timestamp = str(int(time.time()))
    nonce = secrets.token_hex(16)

    params = {"appKey": app_key, "nonce": nonce, "timeStamp": timestamp}
    sorted_params = "&".join(f"{key}={params[key]}" for key in sorted(params))
    signature = hashlib.sha256(f"{sorted_params}{access_token}".encode()).hexdigest()

    share_info = {
        "type": share_request.type,
        "title": share_request.title[:30],
        "content": share_request.content[:1000],
        "images": share_request.images or [],
        "video": share_request.video,
        "cover": share_request.cover,
    }

    verify_config = {
        "appKey": app_key,
        "nonce": nonce,
        "timestamp": timestamp,
        "signature": signature,
    }

    return XhsShareResponse(shareInfo=share_info, verifyConfig=verify_config)
