"""搜索与自动补全接口"""
from fastapi import APIRouter, Query
from services.yfinance_service import search_symbols, get_category_symbols
from utils.api_response import market_meta, success_response

router = APIRouter(prefix="/api", tags=["Search"])


@router.get("/search")
async def search(
    q: str = Query("", max_length=80, description="搜索关键词；为空时返回热门资产"),
    limit: int = Query(15, ge=1, le=50, description="返回结果数量"),
):
    """搜索股票代码/名称"""
    results = search_symbols(q, limit)
    return success_response(
        {"results": results, "query": q},
        market_meta(warnings=[] if results else ["No matching symbol found."]),
    )


@router.get("/categories")
async def categories():
    """获取所有预置分类的标的列表"""
    return success_response(get_category_symbols(), market_meta(source="local+yfinance"))
