"""Research portfolio endpoints."""
from fastapi import APIRouter, HTTPException, Query

from services.research_service import (
    compare_research_portfolio,
    get_research_portfolio,
    list_research_portfolios,
)
from utils.api_response import error_response


router = APIRouter(prefix="/api/research", tags=["Research"])


@router.get("/portfolios")
async def portfolios():
    return list_research_portfolios()


@router.get("/portfolios/{portfolio_id}")
async def portfolio_detail(portfolio_id: str):
    try:
        return get_research_portfolio(portfolio_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=error_response("RESEARCH_PORTFOLIO_NOT_FOUND", str(e)))


@router.get("/portfolios/{portfolio_id}/compare")
async def portfolio_compare(
    portfolio_id: str,
    period: str = Query("1y", pattern="^(1mo|3mo|6mo|1y|2y|5y)$"),
):
    try:
        return compare_research_portfolio(portfolio_id, period)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=error_response("RESEARCH_PORTFOLIO_NOT_FOUND", str(e)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response("RESEARCH_COMPARE_FAILED", str(e)))
