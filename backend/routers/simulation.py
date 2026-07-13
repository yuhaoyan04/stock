"""Virtual account and paper trading endpoints."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.simulation_service import (
    account_response,
    cancel_pending_order,
    get_account_snapshot,
    get_market_status,
    get_pending_orders,
    get_simulation_templates,
    get_trades,
    init_db,
    buy_simulation_template,
    place_order,
    reset_account,
)
from utils.api_response import error_response, market_meta, success_response


router = APIRouter(prefix="/api/simulation", tags=["Simulation"])


class OrderRequest(BaseModel):
    side: str = Field(..., pattern="^(buy|sell)$")
    symbol: str = Field(..., min_length=1, max_length=30)
    quantity: float = Field(..., gt=0)
    price: Optional[float] = Field(None, gt=0)
    fee: Optional[float] = Field(None, ge=0)
    order_type: str = Field("market", pattern="^(market|limit|stop|stop_limit)$")
    limit_price: Optional[float] = Field(None, gt=0)
    stop_price: Optional[float] = Field(None, gt=0)


class TemplateOrderRequest(BaseModel):
    template_id: str = Field(..., min_length=1, max_length=50)
    capital: Optional[float] = Field(None, gt=0)


@router.get("/templates")
async def simulation_templates():
    return success_response(
        {"templates": get_simulation_templates()},
        market_meta(source="static paper-trading templates", warnings=["组合模板仅用于模拟和教学，不构成投资建议。"]),
    )


@router.get("/market-status")
async def market_status():
    try:
        status = get_market_status()
        return success_response(status, market_meta())
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response("MARKET_STATUS_FAILED", str(e)))


@router.get("/account")
async def account_snapshot():
    try:
        init_db()
        return account_response(get_account_snapshot())
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response("SIMULATION_ACCOUNT_FAILED", str(e)))


@router.get("/trades")
async def trade_history(limit: int = Query(100, ge=1, le=500)):
    try:
        return success_response({"trades": get_trades(limit)}, market_meta())
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response("SIMULATION_TRADES_FAILED", str(e)))


@router.get("/orders/pending")
async def get_pending():
    try:
        orders = get_pending_orders()
        return success_response({"orders": orders}, market_meta())
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response("PENDING_ORDERS_FAILED", str(e)))


@router.post("/orders/{order_id}/cancel")
async def cancel_order(order_id: int):
    try:
        result = cancel_pending_order(order_id)
        return success_response(result, market_meta())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=error_response("INVALID_CANCEL", str(e)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response("CANCEL_FAILED", str(e)))


@router.post("/orders")
async def submit_order(payload: OrderRequest):
    try:
        snapshot = place_order(
            side=payload.side,
            symbol=payload.symbol,
            quantity=payload.quantity,
            price=payload.price,
            fee=payload.fee,
            order_type=payload.order_type,
            limit_price=payload.limit_price,
            stop_price=payload.stop_price,
        )
        return account_response(snapshot)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=error_response("INVALID_ORDER", str(e)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response("ORDER_FAILED", str(e)))


@router.post("/template-orders")
async def submit_template_order(payload: TemplateOrderRequest):
    try:
        snapshot = buy_simulation_template(template_id=payload.template_id, capital=payload.capital)
        return account_response(snapshot)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=error_response("INVALID_TEMPLATE_ORDER", str(e)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response("TEMPLATE_ORDER_FAILED", str(e)))


@router.post("/reset")
async def reset_simulation_account():
    try:
        return account_response(reset_account())
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response("SIMULATION_RESET_FAILED", str(e)))
