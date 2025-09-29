import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Query
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.api.errors import error_response
from app.models import Document, DocumentRequest

router = APIRouter()


def _normalize_timestamp(timestamp: datetime) -> datetime:
    """将时间戳标准化为UTC时区。"""

    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=UTC)
    return timestamp.astimezone(UTC)


def _serialize_document(document: Document) -> dict[str, Any]:
    """转换文档对象为与NextJS一致的字段命名。"""

    return {
        "id": str(document.id),
        "title": document.title,
        "content": document.content,
        "kind": document.kind,
        "userId": str(document.user_id),
        "createdAt": document.created_at.isoformat(),
    }


@router.get("/document")
async def get_document(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID = Query(..., description="文档ID"),
) -> Any:
    """
    获取文档
    """
    statement = (
        select(Document)
        .where(Document.id == id, Document.user_id == current_user.id)
        .order_by(Document.created_at.asc())
    )
    result = await db.execute(statement)
    documents = result.all()

    if not documents:
        return error_response("not_found:document")

    return [_serialize_document(document) for document in documents]


@router.post("/document")
async def save_document(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID = Query(..., description="文档ID"),
    document_request: DocumentRequest,
) -> Any:
    """
    保存文档
    """
    statement = select(Document).where(Document.id == id)
    result = await db.execute(statement)
    existing_docs = result.all()

    if existing_docs and existing_docs[0].user_id != current_user.id:
        return error_response("forbidden:document")

    document = Document(
        id=id,
        title=document_request.title,
        content=document_request.content,
        kind=document_request.kind,
        user_id=current_user.id,
        created_at=datetime.now(UTC),
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    return [_serialize_document(document)]


@router.delete("/document")
async def delete_document_versions(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID = Query(..., description="文档ID"),
    timestamp: datetime = Query(..., description="时间戳"),
) -> Any:
    """
    删除指定时间戳之后的文档版本
    """
    statement = select(Document).where(Document.id == id)
    result = await db.execute(statement)
    documents = result.all()

    if not documents:
        return error_response("not_found:document")

    if documents[0].user_id != current_user.id:
        return error_response("forbidden:document")

    normalized_timestamp = _normalize_timestamp(timestamp)
    delete_statement = (
        select(Document)
        .where(
            Document.id == id,
            Document.user_id == current_user.id,
            Document.created_at > normalized_timestamp,
        )
        .order_by(Document.created_at.asc())
    )
    delete_result = await db.execute(delete_statement)
    docs_to_delete = delete_result.all()

    deleted_payload: list[dict[str, Any]] = []
    for doc in docs_to_delete:
        deleted_payload.append(_serialize_document(doc))
        await db.delete(doc)

    await db.commit()

    return deleted_payload
