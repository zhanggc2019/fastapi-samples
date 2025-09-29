"""聊天相关API，与NextJS实现保持兼容。"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import and_, func, select

from app.api.deps import CurrentUser, SessionDep
from app.api.errors import error_response
from app.models import (
    Chat,
    ChatCreate,
    ChatModelId,
    ChatRequest,
    Message,
    MessageRole,
    UserType,
    Visibility,
)

router = APIRouter()

MAX_MESSAGES_PER_DAY = {
    "guest": 20,
    "regular": 100,
}


def _utc_now() -> datetime:
    """返回当前UTC时间，包含时区信息。"""

    return datetime.now(UTC)


def _format_sse(payload: dict[str, Any]) -> str:
    """将字典序列化为SSE数据行。"""

    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _extract_text_content(parts: list[dict[str, Any]]) -> str:
    """提取消息中的文本内容，用于生成标题与简单回复。"""

    texts: list[str] = []
    for part in parts:
        if part.get("type") == "text":
            text = str(part.get("text", "")).strip()
            if text:
                texts.append(text)
    return " ".join(texts)


def _generate_chat_title(message_text: str) -> str:
    """根据首条消息生成聊天标题。"""

    if not message_text:
        return "新对话"
    return message_text[:30]


async def _ensure_message_quota(
    db: SessionDep, user_id: uuid.UUID, user_type: str
) -> bool:
    """检查24小时内的用户消息数量是否超限。"""

    window_start = _utc_now() - timedelta(hours=24)
    # 转换为无时区的时间戳，避免PostgreSQL时区比较错误
    window_start_naive = window_start.replace(tzinfo=None)
    statement = (
        select(func.count(Message.id))
        .join(Chat, Chat.id == Message.chat_id)
        .where(
            and_(
                Chat.user_id == user_id,
                Message.role == MessageRole.USER,
                Message.created_at >= window_start_naive,
            )
        )
    )
    result = await db.execute(statement)
    count = result.scalar_one()
    limit = MAX_MESSAGES_PER_DAY.get(user_type, MAX_MESSAGES_PER_DAY["regular"])
    return count < limit


def _build_usage_payload(
    model: ChatModelId, prompt: str, completion: str
) -> dict[str, Any]:
    """构造用量信息结构，字段与NextJS保持一致。"""

    prompt_tokens = len(prompt.split())
    completion_tokens = len(completion.split())
    total_tokens = prompt_tokens + completion_tokens
    return {
        "modelId": model.value,
        "promptTokens": prompt_tokens,
        "completionTokens": completion_tokens,
        "totalTokens": total_tokens,
    }


async def _persist_assistant_message(
    db: SessionDep,
    chat_id: uuid.UUID,
    text: str,
) -> tuple[uuid.UUID, datetime]:
    """保存AI回复消息并返回元数据。"""

    message_id = uuid.uuid4()
    created_at = _utc_now().replace(tzinfo=None)
    assistant_message = Message(
        id=message_id,
        chat_id=chat_id,
        role=MessageRole.ASSISTANT,
        parts=[{"type": "text", "text": text}],
        attachments=[],
        created_at=created_at,
    )
    db.add(assistant_message)
    await db.commit()
    return message_id, created_at


@router.post("/chat")
async def send_chat_message(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    chat_request: ChatRequest,
) -> Response:
    """处理聊天消息并以SSE推送AI回复。"""

    raw_user_type = getattr(current_user, "user_type", UserType.REGULAR)
    user_type = (
        raw_user_type.value
        if isinstance(raw_user_type, UserType)
        else str(raw_user_type)
    )

    if not await _ensure_message_quota(db, current_user.id, user_type):
        return error_response("rate_limit:chat")

    message_text = _extract_text_content(chat_request.message.parts)

    chat = await db.get(Chat, chat_request.id)
    if chat:
        if chat.user_id != current_user.id:
            return error_response("forbidden:chat")
    else:
        chat_create = ChatCreate(
            title=_generate_chat_title(message_text),
            visibility=chat_request.selectedVisibilityType,
        )
        chat = Chat.model_validate(
            chat_create,
            update={
                "id": chat_request.id,
                "user_id": current_user.id,
                "created_at": _utc_now().replace(tzinfo=None),
            },
        )
        db.add(chat)
        await db.commit()

    user_message = Message(
        id=chat_request.message.id,
        chat_id=chat.id,
        role=chat_request.message.role,
        parts=chat_request.message.parts,
        attachments=[],
        created_at=_utc_now().replace(tzinfo=None),
    )
    db.add(user_message)
    await db.commit()

    assistant_text = (
        "收到消息：" + message_text if message_text else "我已收到你的消息。"
    )
    assistant_message_id, assistant_created_at = await _persist_assistant_message(
        db, chat.id, assistant_text
    )

    usage_payload = _build_usage_payload(
        chat_request.selectedChatModel, message_text, assistant_text
    )
    chat.last_context = usage_payload
    db.add(chat)
    await db.commit()

    assistant_payload = {
        "id": str(assistant_message_id),
        "role": "assistant",
        "parts": [{"type": "text", "text": assistant_text}],
        "metadata": {"createdAt": assistant_created_at.isoformat()},
    }

    async def event_generator() -> AsyncGenerator[str, None]:
        """逐步推送SSE事件。"""

        yield _format_sse(
            {"type": "data-appendMessage", "data": json.dumps(assistant_payload)}
        )
        yield _format_sse({"type": "data-usage", "data": usage_payload})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.delete("/chat")
async def delete_chat(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID = Query(..., description="聊天ID"),
) -> Any:
    """删除聊天并返回删除前的数据。"""

    chat = await db.get(Chat, id)
    if not chat:
        return error_response("not_found:chat")
    if chat.user_id != current_user.id:
        return error_response("forbidden:chat")

    chat_public = {
        "id": str(chat.id),
        "title": chat.title,
        "visibility": chat.visibility.value
        if isinstance(chat.visibility, Visibility)
        else chat.visibility,
        "userId": str(chat.user_id),
        "createdAt": chat.created_at.isoformat(),
        "lastContext": chat.last_context,
    }
    await db.delete(chat)
    await db.commit()
    return chat_public


@router.get("/history")
async def get_chat_history(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    limit: int = 10,
    starting_after: str | None = None,
    ending_before: str | None = None,
) -> Any:
    """分页返回用户聊天列表，与NextJS分页策略一致。"""

    if starting_after and ending_before:
        return error_response(
            "bad_request:api",
            "Only one of starting_after or ending_before can be provided.",
        )

    base_query = select(Chat).where(Chat.user_id == current_user.id)

    if starting_after:
        try:
            anchor_id = uuid.UUID(starting_after)
        except ValueError:
            return error_response(
                "bad_request:api", "Invalid starting_after parameter."
            )
        anchor_chat = await db.get(Chat, anchor_id)
        if not anchor_chat:
            return error_response("not_found:chat")
        base_query = base_query.where(Chat.created_at > anchor_chat.created_at)

    if ending_before:
        try:
            anchor_id = uuid.UUID(ending_before)
        except ValueError:
            return error_response("bad_request:api", "Invalid ending_before parameter.")
        anchor_chat = await db.get(Chat, anchor_id)
        if not anchor_chat:
            return error_response("not_found:chat")
        base_query = base_query.where(Chat.created_at < anchor_chat.created_at)

    statement = base_query.order_by(Chat.created_at.desc()).limit(limit + 1)
    result = await db.execute(statement)
    chats = result.all()

    has_more = len(chats) > limit
    limited_chats = chats[:limit]
    payload = [
        {
            "id": str(item.id),
            "title": item.title,
            "visibility": item.visibility.value
            if isinstance(item.visibility, Visibility)
            else item.visibility,
            "userId": str(item.user_id),
            "createdAt": item.created_at.isoformat(),
            "lastContext": item.last_context,
        }
        for item in limited_chats
    ]
    return {"chats": payload, "hasMore": has_more}


@router.get("/chat/{chat_id}/stream")
async def resume_chat_stream(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    chat_id: uuid.UUID,
) -> Response:
    """恢复最近一次AI回复的流式数据。"""

    chat = await db.get(Chat, chat_id)
    if not chat:
        return error_response("not_found:chat")

    if chat.visibility == Visibility.PRIVATE and chat.user_id != current_user.id:
        return error_response("forbidden:chat")

    message_stmt = (
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
    )
    result = await db.execute(message_stmt)
    messages = result.all()
    if not messages:
        return Response(status_code=204)

    last_message = messages[-1]
    if last_message.role != MessageRole.ASSISTANT:
        return Response(status_code=204)

    if _utc_now() - last_message.created_at > timedelta(seconds=15):
        return Response(status_code=204)

    assistant_payload = {
        "id": str(last_message.id),
        "role": "assistant",
        "parts": last_message.parts,
        "metadata": {"createdAt": last_message.created_at.isoformat()},
    }

    async def stream() -> AsyncGenerator[str, None]:
        """重播最近的AI消息。"""

        yield _format_sse(
            {"type": "data-appendMessage", "data": json.dumps(assistant_payload)}
        )

    return StreamingResponse(stream(), media_type="text/event-stream")
