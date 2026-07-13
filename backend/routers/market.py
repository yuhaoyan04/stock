"""市场总览与多资产对比接口"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from services.yfinance_service import get_market_overview, compare_symbols
from utils.api_response import error_response, market_meta, success_response

router = APIRouter(prefix="/api/market", tags=["Market"])


class CompareRequest(BaseModel):
    symbols: List[str]
    period: str = "1y"


@router.get("/overview")
async def market_overview():
    """获取市场总览 — 主要指数 + 热门股票"""
    try:
        data = get_market_overview()
        warnings = []
        if not data.get("indices"):
            warnings.append("Index overview is empty.")
        if any(item.get("price") is None for item in data.get("indices", [])):
            warnings.append("Some market overview prices are unavailable from yfinance.")
        return success_response(data, market_meta(warnings=warnings))
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response("MARKET_OVERVIEW_FAILED", str(e)))


@router.post("/compare")
async def compare(request: CompareRequest):
    """多资产对比 — 百分比归化的走势对比"""
    if len(request.symbols) < 2:
        raise HTTPException(status_code=400, detail=error_response("INVALID_COMPARE_INPUT", "At least 2 symbols required for comparison"))
    if len(request.symbols) > 10:
        raise HTTPException(status_code=400, detail=error_response("INVALID_COMPARE_INPUT", "Maximum 10 symbols allowed"))

    try:
        data = compare_symbols(request.symbols, request.period)
        warnings = [
            f"{symbol} returned no comparable price series."
            for symbol, series in data.get("series", {}).items()
            if not series
        ]
        return success_response(data, market_meta(warnings=warnings))
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response("COMPARE_FAILED", str(e)))
