import base64
import io
import os
import httpx
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    ImageGenerationRequest, ImageGenerationResponse,
    ContentRewriteRequest, ContentRewriteResponse
)
from core.config import settings

router = APIRouter()


def enhance_prompt_with_style(prompt: str, style: str) -> str:
    """根据风格增强提示词"""
    style_enhancements = {
        "realistic": "photorealistic, high quality, detailed",
        "artistic": "artistic, creative, expressive, painterly",
        "cartoon": "cartoon style, animated, colorful, fun",
        "abstract": "abstract art, conceptual, modern, artistic interpretation",
    }

    enhancement = style_enhancements.get(style, "")
    return f"{prompt}, {enhancement}" if enhancement else prompt


def map_size_to_silicon_flow(size: str) -> str:
    """将尺寸映射到硅基流动支持的格式"""
    size_map = {
        "512x512": "768x1024",
        "768x768": "768x1024",
        "1024x1024": "1024x1024",
    }
    return size_map.get(size, "768x1024")


async def generate_image_with_ai(prompt: str, style: str, size: str) -> Dict[str, Any]:
    """使用硅基流动API生成图片"""
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")

    if not api_key or not base_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Silicon Flow API key or base URL not configured"
        )

    # 根据style调整prompt
    styled_prompt = enhance_prompt_with_style(prompt, style)

    # 确保 baseURL 正确格式化，避免重复的 /v1
    api_url = f"{base_url.rstrip('/v1')}/v1/images/generations"

    # 硅基流动图片生成API调用
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": os.getenv("OPENAI_IMAGE_MODEL_ID", "stabilityai/stable-diffusion-3-medium"),
                    "prompt": styled_prompt,
                    "negative_prompt": "",
                    "seed": 222,
                    "image_size": map_size_to_silicon_flow(size),
                }
            )

            if not response.is_success:
                error_text = await response.aread()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"API错误: HTTP {response.status_code}: {error_text.decode()}"
                )

            data = response.json()

            if not data.get("data") or len(data["data"]) == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="No image generated"
                )

            return data

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="图片生成超时，请稍后重试"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"网络请求错误: {str(e)}"
            )


@router.post("/generate-image", response_model=ImageGenerationResponse)
async def generate_image(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    request: ImageGenerationRequest
) -> Any:
    """
    根据文本描述生成图片
    """
    if not request.prompt or request.prompt.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt is required"
        )

    try:
        # 调用AI图片生成服务
        image_data = await generate_image_with_ai(
            request.prompt,
            request.style or "realistic",
            request.size or "1024x1024"
        )

        return ImageGenerationResponse(
            success=True,
            result=image_data,
            prompt=request.prompt,
            style=request.style or "realistic",
            size=request.size or "1024x1024"
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"图片生成失败: {str(e)}"
        )


@router.post("/rewrite-content", response_model=ContentRewriteResponse)
async def rewrite_content(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    request: ContentRewriteRequest
) -> Any:
    """
    根据指定要求改写文本内容
    """
    try:
        # 这里应该调用实际的文案改写AI服务
        # 目前返回模拟响应
        
        original_content = request.originalContent
        rewrite_type = request.rewriteType
        
        # 模拟改写逻辑
        if rewrite_type == "make_professional":
            rewritten_content = f"经过专业化改写：{original_content}"
        elif rewrite_type == "make_casual":
            rewritten_content = f"经过口语化改写：{original_content}"
        elif rewrite_type == "make_concise":
            rewritten_content = f"简化版：{original_content[:50]}..."
        elif rewrite_type == "make_detailed":
            rewritten_content = f"详细版：{original_content}。这里添加了更多详细信息和解释。"
        elif rewrite_type == "improve_clarity":
            rewritten_content = f"清晰化改写：{original_content}"
        elif rewrite_type == "make_persuasive":
            rewritten_content = f"说服性改写：{original_content}"
        elif rewrite_type == "change_tone":
            tone = request.targetTone or "friendly"
            rewritten_content = f"调整为{tone}语调：{original_content}"
        elif rewrite_type == "fix_grammar":
            rewritten_content = f"语法修正版：{original_content}"
        elif rewrite_type == "translate_style":
            rewritten_content = f"风格转换版：{original_content}"
        else:
            rewritten_content = f"改写版：{original_content}"
        
        return ContentRewriteResponse(
            success=True,
            rewrittenContent=rewritten_content,
            originalContent=original_content,
            rewriteType=rewrite_type,
            targetTone=request.targetTone,
            targetAudience=request.targetAudience,
            originalLength=len(original_content),
            rewrittenLength=len(rewritten_content)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文案改写失败: {str(e)}"
        )
