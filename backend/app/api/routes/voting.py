import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import Vote, VoteRequest, Chat, Message

router = APIRouter()


@router.get("/vote", response_model=List[dict])
async def get_votes(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    chatId: uuid.UUID = Query(..., description="聊天ID")
) -> Any:
    """
    获取指定聊天的投票记录
    """
    # 检查聊天是否存在且属于当前用户
    chat = await db.get(Chat, chatId)
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

    # 查询投票记录
    statement = select(Vote).where(Vote.chat_id == chatId)
    result = await db.exec(statement)
    votes = result.all()

    # 转换为字典格式
    vote_list = []
    for vote in votes:
        vote_list.append({
            "chatId": str(vote.chat_id),
            "messageId": str(vote.message_id),
            "isUpvoted": vote.is_upvoted
        })

    return vote_list


@router.patch("/vote")
async def vote_message(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    vote_request: VoteRequest
) -> Any:
    """
    对消息进行投票
    """
    # 检查聊天是否存在且属于当前用户
    chat = await db.get(Chat, vote_request.chatId)
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

    # 检查消息是否存在且属于指定聊天
    message = await db.get(Message, vote_request.messageId)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在"
        )

    if message.chat_id != vote_request.chatId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="消息不属于指定聊天"
        )

    # 检查是否已经投过票
    statement = select(Vote).where(
        Vote.chat_id == vote_request.chatId,
        Vote.message_id == vote_request.messageId
    )
    result = await db.exec(statement)
    existing_vote = result.first()

    # 确定投票类型
    is_upvoted = vote_request.type == "up"

    if existing_vote:
        # 更新现有投票
        existing_vote.is_upvoted = is_upvoted
        db.add(existing_vote)
    else:
        # 创建新投票
        vote = Vote(
            chat_id=vote_request.chatId,
            message_id=vote_request.messageId,
            is_upvoted=is_upvoted
        )
        db.add(vote)

    await db.commit()

    return {"message": "投票成功"}