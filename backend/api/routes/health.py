"""Health check 端點。"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """確認 API 是否存活。"""
    return {"status": "ok"}
