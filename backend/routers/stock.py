"""个股/资产数据接口"""
from fastapi import APIRouter, Query, HTTPException
from services.yfinance_service import (
    get_stock_info,
    get_stock_history,
    get_financials,
)
from utils.api_response import error_response, market_meta, success_response

router = APIRouter(prefix="/api/stock", tags=["Stock"])


@router.get("/{symbol}/info")
async def stock_info(symbol: str):
    """获取股票/资产详细信息"""
    try:
        info = get_stock_info(symbol)
        if not info.get("name"):
            raise HTTPException(
                status_code=404,
                detail=error_response("INVALID_SYMBOL", f"Symbol '{symbol}' not found or data unavailable"),
            )
        warnings = []
        if info.get("currentPrice") is None:
            warnings.append("Latest price is unavailable from the data source.")
        return success_response(info, market_meta(warnings=warnings))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response("STOCK_INFO_FAILED", str(e)))


@router.get("/{symbol}/history")
async def stock_history(
    symbol: str,
    period: str = Query("1mo", description="时间范围: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max"),
    interval: str = Query("1d", description="数据间隔: 1m,5m,15m,30m,60m,1h,1d,1wk,1mo"),
):
    """获取历史K线数据"""
    try:
        data = get_stock_history(symbol, period=period, interval=interval)
        warnings = [] if data else ["No historical bars returned for this symbol and range."]
        return success_response(
            {"symbol": symbol, "period": period, "interval": interval, "data": data},
            market_meta(warnings=warnings),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response("STOCK_HISTORY_FAILED", str(e)))


@router.get("/{symbol}/financials")
async def stock_financials(
    symbol: str,
    type: str = Query("income", description="报表类型: income, balance, cashflow"),
    period: str = Query("annual", description="周期: annual, quarterly"),
):
    """获取财务报表"""
    try:
        data = get_financials(symbol, statement_type=type, period=period)
        warnings = [] if data else ["Financial statement data is unavailable for this asset."]
        return success_response(
            {"symbol": symbol, "type": type, "period": period, "data": data},
            market_meta(warnings=warnings),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response("FINANCIALS_FAILED", str(e)))
