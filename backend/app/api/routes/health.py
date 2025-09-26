from fastapi import APIRouter
import time
router = APIRouter(prefix="", tags=["health"])


@router.get("/health")
async def health_check():
    return {"status": "ok", "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}