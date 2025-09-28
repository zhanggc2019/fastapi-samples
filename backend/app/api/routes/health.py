import time

from fastapi import APIRouter

router = APIRouter(prefix="", tags=["health"])


@router.get("/health")
async def health_check():
    return {"status": "ok", "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}