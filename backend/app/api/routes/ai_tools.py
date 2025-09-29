import os
from typing import Any

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    ContentRewriteRequest,
    ContentRewriteResponse,
    ImageGenerationRequest,
    ImageGenerationResponse,
)

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


class ImageGenerationError(RuntimeError):
    """图片生成过程中产生的业务异常。"""


async def generate_image_with_ai(prompt: str, style: str, size: str) -> dict[str, Any]:
    """使用硅基流动API生成图片"""
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")

    if not api_key or not base_url:
        raise ImageGenerationError("Silicon Flow API key or base URL not configured")

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
                    "model": os.getenv(
                        "OPENAI_IMAGE_MODEL_ID", "stabilityai/stable-diffusion-3-medium"
                    ),
                    "prompt": styled_prompt,
                    "negative_prompt": "",
                    "seed": 222,
                    "image_size": map_size_to_silicon_flow(size),
                },
            )

            if not response.is_success:
                error_text = await response.aread()
                raise ImageGenerationError(
                    f"API错误: HTTP {response.status_code}: {error_text.decode()}"
                )

            data = response.json()
            print(data)

            if not data.get("data") or len(data["data"]) == 0:
                raise ImageGenerationError("No image generated")

            return data

        except httpx.TimeoutException:
            raise ImageGenerationError("图片生成超时，请稍后重试")
        except httpx.RequestError as exc:
            raise ImageGenerationError(f"网络请求错误: {exc}")


@router.post("/generate-image", response_model=ImageGenerationResponse)
async def generate_image(
    *, _db: SessionDep, _current_user: CurrentUser, request: ImageGenerationRequest
) -> Any:
    """
    根据文本描述生成图片
    """
    if not request.prompt or request.prompt.strip() == "":
        return JSONResponse(
            status_code=400,
            content={"error": "Prompt is required"},
        )

    try:
        image_data = await generate_image_with_ai(
            request.prompt,
            request.style or "realistic",
            request.size or "1024x1024",
        )
    except ImageGenerationError as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})

    response = ImageGenerationResponse(
        result=image_data,
        prompt=request.prompt,
        style=request.style or "realistic",
        size=request.size or "1024x1024",
    )
    return response


@router.post("/rewrite-content", response_model=ContentRewriteResponse)
async def rewrite_content(
    *, _db: SessionDep, _current_user: CurrentUser, request: ContentRewriteRequest
) -> Any:
    """
    根据指定要求改写文本内容
    """
    if not request.originalContent or not request.originalContent.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Original content is required"},
        )

    try:
        original_content = request.originalContent
        rewrite_type = request.rewriteType

        if rewrite_type == "make_professional":
            rewritten_content = f"专业化版本：{original_content}"
        elif rewrite_type == "make_casual":
            rewritten_content = f"口语化版本：{original_content}"
        elif rewrite_type == "make_concise":
            rewritten_content = original_content[:200].strip() + (
                "..." if len(original_content) > 200 else ""
            )
        elif rewrite_type == "make_detailed":
            rewritten_content = (
                f"详细说明：{original_content}\n\n更多补充内容可在此处追加。"
            )
        elif rewrite_type == "improve_clarity":
            rewritten_content = f"清晰表述：{original_content}"
        elif rewrite_type == "make_persuasive":
            rewritten_content = f"说服力增强：{original_content}"
        elif rewrite_type == "change_tone":
            tone = request.targetTone or "friendly"
            rewritten_content = f"{tone} 语气的版本：{original_content}"
        elif rewrite_type == "fix_grammar":
            rewritten_content = f"语法优化：{original_content}"
        elif rewrite_type == "translate_style":
            rewritten_content = f"风格改写：{original_content}"
        else:
            rewritten_content = f"改写内容：{original_content}"

        return ContentRewriteResponse(
            success=True,
            rewrittenContent=rewritten_content,
            originalContent=original_content,
            rewriteType=rewrite_type,
            targetTone=request.targetTone,
            targetAudience=request.targetAudience,
            originalLength=len(original_content),
            rewrittenLength=len(rewritten_content),
        )
    except Exception as exc:  # noqa: BLE001 - 返回统一错误提示
        return JSONResponse(
            status_code=500,
            content={"error": f"文案改写失败: {exc}"},
        )
