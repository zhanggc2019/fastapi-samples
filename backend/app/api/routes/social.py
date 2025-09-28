from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import SessionDep
from app.models import XhsShareRequest, XhsShareResponse

router = APIRouter()


@router.post("/xhs/share-config", response_model=XhsShareResponse)
async def create_xhs_share_config(
    *,
    db: SessionDep,
    share_request: XhsShareRequest
) -> Any:
    """
    生成小红书分享配置
    """
    try:
        # 验证请求数据
        if not share_request.title or len(share_request.title) > 60:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="标题长度必须在1-60字符之间"
            )
        
        if not share_request.content or len(share_request.content) > 2000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="内容长度必须在1-2000字符之间"
            )
        
        # 生成分享配置
        share_info = {
            "type": share_request.type,
            "title": share_request.title,
            "content": share_request.content,
            "images": share_request.images or [],
            "video": share_request.video,
            "cover": share_request.cover,
            "platform": "xiaohongshu",
            "timestamp": "2025-09-28T16:00:00Z",
            "shareUrl": f"https://xiaohongshu.com/share/{share_request.type}",
            "qrCode": f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={share_request.title}",
            "tags": ["AI生成", "智能分享"],
            "category": "科技"
        }
        
        return XhsShareResponse(
            success=True,
            shareInfo=share_info
        )
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成分享配置失败: {str(e)}"
        )
