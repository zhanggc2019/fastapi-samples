import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import Chat, ChatCreate, ChatPublic, ChatRequest, Message

router = APIRouter()


@router.post("/chat", response_model=None)
async def send_chat_message(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    chat_request: ChatRequest
) -> StreamingResponse:
    """
    发送聊天消息并获取AI回复的流式响应
    """
    # 检查聊天是否存在，如果不存在则创建
    chat = await db.get(Chat, chat_request.id)
    if not chat:
        chat_create = ChatCreate(
            title="新对话",
            visibility=chat_request.selectedVisibilityType
        )
        chat = Chat.model_validate(chat_create, update={"user_id": current_user.id, "id": chat_request.id})
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
    
    # 创建用户消息，使用Message表（对应Message_v2表）存储完整的parts和attachments
    message = Message(
        id=chat_request.message.id,
        role=chat_request.message.role,
        parts=chat_request.message.parts,
        attachments=[],  # 暂时为空，后续可以添加附件支持
        chat_id=chat.id
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    # 模拟AI响应流
    async def generate_response():
        # 这里应该调用实际的AI服务
        # 目前返回模拟响应
        response_text = f"这是对消息 '{chat_request.message.parts[0].text}' 的AI回复"
        
        # 模拟流式响应
        for chunk in response_text.split():
            yield f"data: {chunk} \n\n"
        
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/chat/{chat_id}/stream")
async def resume_chat_stream(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    chat_id: uuid.UUID
) -> StreamingResponse:
    """
    恢复指定聊天的流式响应
    """
    # 检查聊天是否存在且属于当前用户
    chat = await db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天不存在"
        )
    
    if chat.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此聊天"
        )

    # 检查是否有未完成的流
    # 这里应该检查实际的流状态
    # 目前返回204表示无内容
    raise HTTPException(
        status_code=status.HTTP_204_NO_CONTENT,
        detail="无活动流"
    )


@router.get("/history", response_model=list[ChatPublic])
async def get_chat_history(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    limit: int = 10,
    starting_after: str = None,
    ending_before: str = None
) -> Any:
    """
    获取用户的聊天历史记录
    """
    # 构建查询
    statement = select(Chat).where(Chat.user_id == current_user.id)
    
    # 添加分页逻辑
    if starting_after:
        try:
            starting_id = uuid.UUID(starting_after)
            statement = statement.where(Chat.id > starting_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的starting_after参数"
            )
    
    if ending_before:
        try:
            ending_id = uuid.UUID(ending_before)
            statement = statement.where(Chat.id < ending_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的ending_before参数"
            )
    
    # 限制数量并按创建时间倒序
    statement = statement.order_by(Chat.created_at.desc()).limit(limit)
    
    result = await db.exec(statement)
    chats = result.all()
    return chats


@router.get("/chat/{id}/stream")
async def get_chat_stream(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID
) -> StreamingResponse:
    """
    恢复指定聊天的流式响应
    """
    # 检查聊天是否存在且属于当前用户
    chat = await db.get(Chat, id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天不存在"
        )

    if chat.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此聊天"
        )

    # 检查是否有未完成的流
    # 这里简化处理，返回204表示无内容
    async def empty_stream():
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        empty_stream(),
        media_type="text/event-stream",
        status_code=204
    )
