from fastapi import APIRouter

from app.api.routes import chat, ai_tools, auth, files, documents, voting, suggestions, social
from core.config import settings

api_router = APIRouter()

# 根据chat.json包含所有14个API接口
api_router.include_router(chat.router, tags=["Chat"])                    # /api/chat, /api/chat/{id}/stream, /api/history
api_router.include_router(ai_tools.router, tags=["AI Tools"])           # /api/generate-image, /api/rewrite-content
api_router.include_router(files.router, tags=["Files"])                 # /api/files/upload
api_router.include_router(documents.router, tags=["Documents"])         # /api/document (GET/POST/DELETE)
api_router.include_router(voting.router, tags=["Voting"])               # /api/vote (GET/PATCH)
api_router.include_router(suggestions.router, tags=["Suggestions"])     # /api/suggestions
api_router.include_router(social.router, tags=["Social"])               # /api/xhs/share-config
api_router.include_router(auth.router, tags=["Authentication"])         # /api/auth/guest

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
