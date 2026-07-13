"""组合与回测接口"""
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.portfolio_service import backtest_portfolio
from utils.api_response import error_response


router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])


class BacktestRequest(BaseModel):
    symbols: List[str] = Field(..., min_length=1, max_length=20)
    period: str = Field("1y", pattern="^(1mo|3mo|6mo|1y|2y|5y|10y|max)$")
    mode: str = Field("equal", pattern="^(equal|custom|risk_parity|min_variance|max_sharpe)$")
    weights: Optional[Dict[str, float]] = None
    benchmark: str = "SPY"


@router.post("/backtest")
async def portfolio_backtest(payload: BacktestRequest):
    """运行组合回测并返回净值、回撤、权重和指标"""
    try:
        return backtest_portfolio(
            symbols=payload.symbols,
            period=payload.period,
            mode=payload.mode,
            weights=payload.weights,
            benchmark=payload.benchmark,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=error_response("INVALID_BACKTEST_INPUT", str(e)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response("BACKTEST_FAILED", str(e)))
