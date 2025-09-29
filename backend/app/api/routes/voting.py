import uuid
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import Response
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.api.errors import error_response
from app.models import Chat, Message, Vote, VoteRequest

router = APIRouter()


@router.get("/vote")
async def get_votes(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    chatId: uuid.UUID = Query(..., description="聊天ID"),
) -> Any:
    """
    获取指定聊天的投票记录
    """
    chat = await db.get(Chat, chatId)
    if not chat:
        return error_response("not_found:chat")

    if chat.user_id != current_user.id:
        return error_response("forbidden:vote")

    # 查询投票记录
    statement = select(Vote).where(Vote.chat_id == chatId)
    result = await db.execute(statement)
    votes = result.all()

    vote_list: list[dict[str, Any]] = []
    for vote in votes:
        vote_list.append(
            {
                "chatId": str(vote.chat_id),
                "messageId": str(vote.message_id),
                "isUpvoted": vote.is_upvoted,
            }
        )

    return vote_list


@router.patch("/vote")
async def vote_message(
    *, db: SessionDep, current_user: CurrentUser, vote_request: VoteRequest
) -> Any:
    """
    对消息进行投票
    """
    chat = await db.get(Chat, vote_request.chatId)
    if not chat:
        return error_response("not_found:chat")

    if chat.user_id != current_user.id:
        return error_response("forbidden:vote")

    # 检查消息是否存在且属于指定聊天
    message = await db.get(Message, vote_request.messageId)
    if not message:
        return error_response("not_found:vote")

    if message.chat_id != vote_request.chatId:
        return error_response("bad_request:api", "Message does not belong to chat")

    # 检查是否已经投过票
    statement = select(Vote).where(
        Vote.chat_id == vote_request.chatId, Vote.message_id == vote_request.messageId
    )
    result = await db.execute(statement)
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
            is_upvoted=is_upvoted,
        )
        db.add(vote)

    await db.commit()

    return Response(content="Message voted", media_type="text/plain")
