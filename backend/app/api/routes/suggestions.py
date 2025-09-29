import uuid
from typing import Any

from fastapi import APIRouter, Query
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.api.errors import error_response
from app.models import Suggestion

router = APIRouter()


@router.get("/suggestions")
async def get_suggestions(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    documentId: uuid.UUID = Query(..., description="文档ID"),
) -> Any:
    """
    获取文档的建议列表
    """
    suggestion_statement = (
        select(Suggestion)
        .where(Suggestion.document_id == documentId)
        .order_by(Suggestion.created_at.desc())
    )

    suggestion_result = await db.execute(suggestion_statement)
    suggestions = suggestion_result.all()

    if not suggestions:
        return []

    first_suggestion = suggestions[0]
    if first_suggestion.user_id != current_user.id:
        return error_response("forbidden:api")

    suggestion_list: list[dict[str, Any]] = []
    for suggestion in suggestions:
        suggestion_list.append(
            {
                "id": str(suggestion.id),
                "originalText": suggestion.original_text,
                "suggestedText": suggestion.suggested_text,
                "description": suggestion.description,
                "isResolved": suggestion.is_resolved,
                "documentId": str(suggestion.document_id),
                "documentCreatedAt": suggestion.document_created_at.isoformat(),
                "userId": str(suggestion.user_id),
                "createdAt": suggestion.created_at.isoformat(),
            }
        )

    return suggestion_list
