import uuid
from datetime import datetime
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import Document, DocumentCreate, DocumentPublic, DocumentRequest

router = APIRouter()


@router.get("/document", response_model=List[DocumentPublic])
async def get_document(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID = Query(..., description="文档ID")
) -> Any:
    """
    获取文档
    """
    # 查询文档
    statement = select(Document).where(
        Document.id == id,
        Document.user_id == current_user.id
    ).order_by(Document.created_at.desc())
    
    result = await db.exec(statement)
    documents = result.all()
    
    if not documents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )
    
    return documents


@router.post("/document", response_model=DocumentPublic)
async def save_document(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID = Query(..., description="文档ID"),
    document_request: DocumentRequest
) -> Any:
    """
    保存文档
    """
    # 检查是否已存在文档
    statement = select(Document).where(
        Document.id == id,
        Document.user_id == current_user.id
    )
    result = await db.exec(statement)
    existing_docs = result.all()
    
    # 如果存在文档，检查权限
    if existing_docs:
        first_doc = existing_docs[0]
        if first_doc.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此文档"
            )
    
    # 创建新文档版本
    document = Document(
        id=id,
        title=document_request.title,
        content=document_request.content,
        kind=document_request.kind,
        user_id=current_user.id,
        created_at=datetime.utcnow()
    )
    
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    return document


@router.delete("/document", response_model=List[DocumentPublic])
async def delete_document_versions(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID = Query(..., description="文档ID"),
    timestamp: datetime = Query(..., description="时间戳")
) -> Any:
    """
    删除指定时间戳之后的文档版本
    """
    # 检查文档权限
    statement = select(Document).where(
        Document.id == id,
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
    
    # 删除指定时间戳之后的版本
    delete_statement = select(Document).where(
        Document.id == id,
        Document.user_id == current_user.id,
        Document.created_at > timestamp
    )
    delete_result = await db.exec(delete_statement)
    docs_to_delete = delete_result.all()
    
    for doc in docs_to_delete:
        await db.delete(doc)
    
    await db.commit()
    
    # 返回剩余的文档版本
    remaining_statement = select(Document).where(
        Document.id == id,
        Document.user_id == current_user.id
    ).order_by(Document.created_at.desc())
    
    remaining_result = await db.exec(remaining_statement)
    remaining_docs = remaining_result.all()
    
    return remaining_docs
