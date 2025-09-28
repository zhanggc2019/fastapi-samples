import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import Suggestion, Document

router = APIRouter()


@router.get("/suggestions", response_model=List[dict])
async def get_suggestions(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    documentId: uuid.UUID = Query(..., description="文档ID")
) -> Any:
    """
    获取文档的建议列表
    """
    # 检查文档是否存在且属于当前用户
    statement = select(Document).where(
        Document.id == documentId,
        Document.user_id == current_user.id
    )
    result = await db.exec(statement)
    documents = result.all()
    
    if not documents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )
    
    # 检查权限
    first_doc = documents[0]
    if first_doc.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此文档"
        )
    
    # 查询建议
    suggestion_statement = select(Suggestion).where(
        Suggestion.document_id == documentId,
        Suggestion.user_id == current_user.id
    ).order_by(Suggestion.created_at.desc())
    
    suggestion_result = await db.exec(suggestion_statement)
    suggestions = suggestion_result.all()
    
    # 转换为字典格式
    suggestion_list = []
    for suggestion in suggestions:
        suggestion_list.append({
            "id": str(suggestion.id),
            "originalText": suggestion.original_text,
            "suggestedText": suggestion.suggested_text,
            "description": suggestion.description,
            "isResolved": suggestion.is_resolved,
            "documentId": str(suggestion.document_id),
            "documentCreatedAt": suggestion.document_created_at.isoformat(),
            "userId": str(suggestion.user_id),
            "createdAt": suggestion.created_at.isoformat()
        })
    
    return suggestion_list
