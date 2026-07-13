"""Macro and policy news endpoints."""
from fastapi import APIRouter, HTTPException
from services.news_service import get_daily_briefing
from utils.api_response import error_response

router = APIRouter(prefix="/api/news", tags=["News"])


@router.get("/daily-briefing")
async def daily_briefing():
    try:
        return get_daily_briefing()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=error_response("NEWS_BRIEFING_FAILED", "资讯服务暂时不可用，请稍后重试。")) from exc
