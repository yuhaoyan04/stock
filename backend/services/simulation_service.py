"""Virtual account persistence and trading service."""
import sqlite3
from datetime import datetime, timezone, date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from services.yfinance_service import get_stock_info
from utils.api_response import market_meta, success_response


DB_PATH = Path(__file__).resolve().parents[1] / "simulation.db"
INITIAL_CASH = 100000.0
DEFAULT_ACCOUNT_ID = 1

SIMULATION_TEMPLATES = [
    {
        "id": "classic_60_40",
        "name": "经典 60/40",
        "style": "基金 / ETF",
        "description": "用宽基股票和中长期债券演示传统资产配置。",
        "holdings": [{"symbol": "SPY", "name": "标普500 ETF", "weight": 0.60}, {"symbol": "AGG", "name": "美国综合债券 ETF", "weight": 0.40}],
    },
    {
        "id": "all_weather",
        "name": "全天候风格",
        "style": "Ray Dalio 风格",
        "description": "用股票、债券、黄金和商品分散不同宏观环境风险。",
        "holdings": [{"symbol": "SPY", "name": "标普500 ETF", "weight": 0.30}, {"symbol": "TLT", "name": "长期美债 ETF", "weight": 0.40}, {"symbol": "GLD", "name": "黄金 ETF", "weight": 0.15}, {"symbol": "DBC", "name": "商品 ETF", "weight": 0.15}],
    },
    {
        "id": "buffett_core",
        "name": "巴菲特式核心",
        "style": "长期价值风格",
        "description": "以低成本标普500 ETF 为核心，加入少量现金管理工具。",
        "holdings": [{"symbol": "VOO", "name": "Vanguard S&P 500 ETF", "weight": 0.85}, {"symbol": "BRK-B", "name": "Berkshire Hathaway B", "weight": 0.10}, {"symbol": "BIL", "name": "短期国债 ETF", "weight": 0.05}],
    },
    {
        "id": "global_diversified",
        "name": "全球分散组合",
        "style": "基金 / ETF",
        "description": "用美国、国际股票和债券建立一个易于理解的全球组合。",
        "holdings": [{"symbol": "VTI", "name": "美国全市场 ETF", "weight": 0.45}, {"symbol": "VXUS", "name": "美国以外国际股票 ETF", "weight": 0.25}, {"symbol": "BND", "name": "美国债券 ETF", "weight": 0.20}, {"symbol": "GLD", "name": "黄金 ETF", "weight": 0.10}],
    },
]


def _connect(db_path: Optional[Path] = None) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path or DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db(db_path: Optional[Path] = None) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY,
                cash REAL NOT NULL,
                realized_pnl REAL NOT NULL DEFAULT 0,
                initial_cash REAL NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS positions (
                account_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                average_cost REAL NOT NULL,
                realized_pnl REAL NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (account_id, symbol)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                side TEXT NOT NULL,
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                fee REAL NOT NULL,
                gross_amount REAL NOT NULL,
                net_cash_change REAL NOT NULL,
                realized_pnl REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pending_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                order_type TEXT NOT NULL,
                side TEXT NOT NULL,
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                limit_price REAL,
                stop_price REAL,
                fee REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                reject_reason TEXT,
                filled_price REAL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                filled_at TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                snapshot_date TEXT NOT NULL,
                total_assets REAL NOT NULL,
                cash REAL NOT NULL,
                holdings_value REAL NOT NULL,
                cumulative_pnl REAL NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(account_id, snapshot_date)
            )
            """
        )

        row = conn.execute("SELECT id FROM accounts WHERE id = ?", (DEFAULT_ACCOUNT_ID,)).fetchone()
        if row is None:
            now = _now_iso()
            conn.execute(
                "INSERT INTO accounts (id, cash, realized_pnl, initial_cash, created_at, updated_at) VALUES (?, ?, 0, ?, ?, ?)",
                (DEFAULT_ACCOUNT_ID, INITIAL_CASH, INITIAL_CASH, now, now),
            )
        conn.commit()


def _safe_float(value: Any, digits: int = 4) -> Optional[float]:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return round(number, digits)


def _normalize_symbol(symbol: str) -> str:
    normalized = str(symbol or "").strip().upper()
    if not normalized:
        raise ValueError("ticker cannot be empty")
    return normalized


def get_market_status() -> Dict[str, Any]:
    """Return US stock market status based on current Eastern time."""
    ny_tz = ZoneInfo("America/New_York")
    now_ny = datetime.now(ny_tz)
    is_weekday = now_ny.weekday() < 5  # 0=Monday..4=Friday

    market_open = now_ny.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now_ny.replace(hour=16, minute=0, second=0, microsecond=0)

    if not is_weekday:
        return {"isOpen": False, "status": "closed", "label": "Closed (Weekend)"}
    if now_ny < market_open:
        return {"isOpen": False, "status": "pre_market", "label": "Pre-Market"}
    if now_ny > market_close:
        return {"isOpen": False, "status": "after_hours", "label": "After-Hours"}
    return {"isOpen": True, "status": "open", "label": "Market Open"}


def calculate_default_fee(quantity: float, price: float) -> float:
    """Auto-calculate a representative trading fee (SEC fee ~0.00278% of trade value, min $0.01)."""
    trade_value = quantity * price
    fee = trade_value * 0.0000278
    return round(max(fee, 0.01), 4)


def get_simulation_templates() -> List[Dict[str, Any]]:
    return [dict(template, holdings=[dict(item) for item in template["holdings"]]) for template in SIMULATION_TEMPLATES]


def _latest_price(symbol: str) -> Dict[str, Any]:
    info = get_stock_info(symbol)
    price = info.get("currentPrice") or info.get("previousClose")
    if price is None or float(price) <= 0:
        raise ValueError(f"latest price unavailable for {symbol}")
    return {
        "symbol": info.get("symbol") or symbol,
        "name": info.get("name") or symbol,
        "price": float(price),
        "previousClose": float(info.get("previousClose", 0) or 0),
        "currency": info.get("currency") or "USD",
        "exchange": info.get("exchange") or "",
    }


def _get_account(conn: sqlite3.Connection) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM accounts WHERE id = ?", (DEFAULT_ACCOUNT_ID,)).fetchone()
    if row is None:
        now = _now_iso()
        conn.execute(
            "INSERT INTO accounts (id, cash, realized_pnl, initial_cash, created_at, updated_at) VALUES (?, ?, 0, ?, ?, ?)",
            (DEFAULT_ACCOUNT_ID, INITIAL_CASH, INITIAL_CASH, now, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM accounts WHERE id = ?", (DEFAULT_ACCOUNT_ID,)).fetchone()
    return row


def _get_position(conn: sqlite3.Connection, symbol: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM positions WHERE account_id = ? AND symbol = ?",
        (DEFAULT_ACCOUNT_ID, symbol),
    ).fetchone()


def _execute_trade(
    conn: sqlite3.Connection,
    side: str,
    symbol: str,
    quantity: float,
    price: float,
    fee: float = 0.0,
) -> Dict[str, Any]:
    """Execute a trade against an open connection. Returns cash_change and realized_pnl."""
    account = _get_account(conn)
    cash = float(account["cash"])
    position = _get_position(conn, symbol)
    current_qty = float(position["quantity"]) if position else 0.0
    average_cost = float(position["average_cost"]) if position else 0.0
    realized_pnl = 0.0
    gross_amount = price * quantity

    if side == "buy":
        total_cost = gross_amount + fee
        if cash + 1e-8 < total_cost:
            raise ValueError("insufficient cash for buy order")
        new_qty = current_qty + quantity
        new_average_cost = ((current_qty * average_cost) + gross_amount + fee) / new_qty
        cash_change = -total_cost
        conn.execute(
            """
            INSERT INTO positions (account_id, symbol, quantity, average_cost, realized_pnl, updated_at)
            VALUES (?, ?, ?, ?, COALESCE((SELECT realized_pnl FROM positions WHERE account_id = ? AND symbol = ?), 0), ?)
            ON CONFLICT(account_id, symbol) DO UPDATE SET
                quantity = excluded.quantity,
                average_cost = excluded.average_cost,
                updated_at = excluded.updated_at
            """,
            (DEFAULT_ACCOUNT_ID, symbol, new_qty, new_average_cost, DEFAULT_ACCOUNT_ID, symbol, _now_iso()),
        )
    else:
        if current_qty + 1e-8 < quantity:
            raise ValueError("insufficient holdings for sell order")
        proceeds = gross_amount - fee
        realized_pnl = (price - average_cost) * quantity - fee
        cash_change = proceeds
        new_qty = current_qty - quantity
        if new_qty <= 1e-8:
            conn.execute(
                "DELETE FROM positions WHERE account_id = ? AND symbol = ?",
                (DEFAULT_ACCOUNT_ID, symbol),
            )
        else:
            conn.execute(
                """
                UPDATE positions
                SET quantity = ?, realized_pnl = realized_pnl + ?, updated_at = ?
                WHERE account_id = ? AND symbol = ?
                """,
                (new_qty, realized_pnl, _now_iso(), DEFAULT_ACCOUNT_ID, symbol),
            )

    now = _now_iso()
    conn.execute(
        "UPDATE accounts SET cash = cash + ?, realized_pnl = realized_pnl + ?, updated_at = ? WHERE id = ?",
        (cash_change, realized_pnl, now, DEFAULT_ACCOUNT_ID),
    )
    conn.execute(
        """
        INSERT INTO trades (account_id, side, symbol, quantity, price, fee, gross_amount, net_cash_change, realized_pnl, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (DEFAULT_ACCOUNT_ID, side, symbol, quantity, price, fee, gross_amount, cash_change, realized_pnl, now),
    )
    return {"cash_change": cash_change, "realized_pnl": realized_pnl}


def reset_account(db_path: Optional[Path] = None, refresh_prices: bool = True) -> Dict[str, Any]:
    init_db(db_path)
    with _connect(db_path) as conn:
        now = _now_iso()
        conn.execute("DELETE FROM trades WHERE account_id = ?", (DEFAULT_ACCOUNT_ID,))
        conn.execute("DELETE FROM positions WHERE account_id = ?", (DEFAULT_ACCOUNT_ID,))
        conn.execute("DELETE FROM pending_orders WHERE account_id = ?", (DEFAULT_ACCOUNT_ID,))
        conn.execute("DELETE FROM daily_snapshots WHERE account_id = ?", (DEFAULT_ACCOUNT_ID,))
        conn.execute(
            "UPDATE accounts SET cash = ?, realized_pnl = 0, initial_cash = ?, updated_at = ? WHERE id = ?",
            (INITIAL_CASH, INITIAL_CASH, now, DEFAULT_ACCOUNT_ID),
        )
        conn.commit()
    return get_account_snapshot(db_path=db_path, refresh_prices=refresh_prices)


def place_order(
    side: str,
    symbol: str,
    quantity: float,
    price: Optional[float] = None,
    fee: Optional[float] = None,
    order_type: str = "market",
    limit_price: Optional[float] = None,
    stop_price: Optional[float] = None,
    db_path: Optional[Path] = None,
    refresh_prices: bool = True,
) -> Dict[str, Any]:
    init_db(db_path)
    clean_side = str(side or "").strip().lower()
    if clean_side not in {"buy", "sell"}:
        raise ValueError("side must be buy or sell")
    clean_symbol = _normalize_symbol(symbol)
    clean_order_type = str(order_type or "").strip().lower()
    if clean_order_type not in {"market", "limit", "stop", "stop_limit"}:
        raise ValueError("order_type must be market, limit, stop, or stop_limit")

    try:
        qty = float(quantity)
        order_fee = None if fee is None else float(fee)
    except (TypeError, ValueError):
        raise ValueError("quantity and fee must be numbers")
    if qty <= 0:
        raise ValueError("quantity must be greater than 0")
    if order_fee is not None and order_fee < 0:
        raise ValueError("fee cannot be negative")

    # Validate order-type-specific fields
    if clean_order_type in ("limit", "stop_limit"):
        if limit_price is None or float(limit_price) <= 0:
            raise ValueError("limit_price is required for limit/stop-limit orders")
    if clean_order_type in ("stop", "stop_limit"):
        if stop_price is None or float(stop_price) <= 0:
            raise ValueError("stop_price is required for stop/stop-limit orders")

    # Get quote for market orders (or when price not provided)
    quote = None
    if price is not None and float(price) > 0:
        trade_price = float(price)
        quote = {"symbol": clean_symbol, "name": clean_symbol, "price": trade_price, "previousClose": 0, "currency": "USD", "exchange": ""}
    elif clean_order_type == "market":
        quote = _latest_price(clean_symbol)
        trade_price = float(quote["price"])
    else:
        # For non-market orders without explicit price, fetch quote for auto-fee
        quote = _latest_price(clean_symbol)
        trade_price = float(limit_price or stop_price or quote["price"])

    if trade_price <= 0:
        raise ValueError("price must be greater than 0")

    # Auto-calculate fee if not provided
    if order_fee is None:
        order_fee = calculate_default_fee(qty, trade_price)

    with _connect(db_path) as conn:
        if clean_order_type == "market":
            # Execute immediately
            try:
                _execute_trade(conn, clean_side, clean_symbol, qty, trade_price, order_fee)
                conn.commit()
            except ValueError:
                raise
        else:
            # Insert pending order
            now = _now_iso()
            conn.execute(
                """
                INSERT INTO pending_orders
                (account_id, order_type, side, symbol, quantity, limit_price, stop_price, fee, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                """,
                (
                    DEFAULT_ACCOUNT_ID, clean_order_type, clean_side, clean_symbol,
                    qty,
                    _safe_float(limit_price) if limit_price is not None else None,
                    _safe_float(stop_price) if stop_price is not None else None,
                    order_fee, now, now,
                ),
            )
            conn.commit()

    return get_account_snapshot(db_path=db_path, refresh_prices=refresh_prices)


def buy_simulation_template(
    template_id: str,
    capital: Optional[float] = None,
    db_path: Optional[Path] = None,
    refresh_prices: bool = True,
) -> Dict[str, Any]:
    """Buy a paper portfolio using fractional shares and the existing trade checks."""
    template = next((item for item in SIMULATION_TEMPLATES if item["id"] == template_id), None)
    if template is None:
        raise ValueError("simulation template not found")
    init_db(db_path)
    warnings: List[str] = []
    executed: List[Dict[str, Any]] = []
    with _connect(db_path) as conn:
        account = _get_account(conn)
        available_cash = float(account["cash"])
        budget = available_cash if capital is None else float(capital)
        if budget <= 0:
            raise ValueError("template capital must be greater than 0")
        if budget > available_cash + 1e-8:
            raise ValueError("template capital cannot exceed available cash")
        for holding in template["holdings"]:
            try:
                quote = _latest_price(holding["symbol"])
                price = float(quote["price"])
                target_amount = budget * float(holding["weight"])
                fee = calculate_default_fee(max(target_amount / price, 0.000001), price)
                quantity = max((target_amount - fee) / price, 0)
                if quantity <= 0:
                    warnings.append(f"{holding['symbol']} 配置金额过小，已跳过")
                    continue
                _execute_trade(conn, "buy", holding["symbol"], quantity, price, fee)
                executed.append({"symbol": holding["symbol"], "quantity": round(quantity, 6), "price": price, "weight": holding["weight"]})
            except Exception as exc:
                warnings.append(f"{holding['symbol']} 暂时无法买入：{exc}")
        if not executed:
            raise ValueError("template has no executable holdings: " + "; ".join(warnings))
        conn.commit()

    snapshot = get_account_snapshot(db_path=db_path, refresh_prices=refresh_prices)
    snapshot["templateExecution"] = {"templateId": template_id, "templateName": template["name"], "executed": executed}
    snapshot["warnings"] = [*snapshot.get("warnings", []), *warnings]
    return snapshot


def _process_pending_orders(conn: sqlite3.Connection) -> List[str]:
    """Evaluate all pending orders against current prices. Returns list of warnings."""
    warnings = []
    pending_rows = conn.execute(
        "SELECT * FROM pending_orders WHERE account_id = ? AND status = 'pending' ORDER BY id ASC",
        (DEFAULT_ACCOUNT_ID,),
    ).fetchall()

    for row in pending_rows:
        order_id = row["id"]
        order_type = row["order_type"]
        p_side = row["side"]
        p_symbol = row["symbol"]
        p_qty = float(row["quantity"])
        p_limit = float(row["limit_price"]) if row["limit_price"] is not None else None
        p_stop = float(row["stop_price"]) if row["stop_price"] is not None else None
        p_fee = float(row["fee"])

        try:
            quote = _latest_price(p_symbol)
            current_price = quote["price"]
        except Exception as exc:
            warnings.append(f"pending order #{order_id} ({p_symbol}): cannot fetch price — {exc}")
            continue

        triggered = False
        filled_price = current_price

        if order_type == "limit":
            if p_side == "buy" and current_price <= p_limit:
                triggered = True
                filled_price = min(current_price, p_limit)
            elif p_side == "sell" and current_price >= p_limit:
                triggered = True
                filled_price = max(current_price, p_limit)
        elif order_type == "stop":
            if p_side == "buy" and current_price >= p_stop:
                triggered = True
            elif p_side == "sell" and current_price <= p_stop:
                triggered = True
        elif order_type == "stop_limit":
            stop_triggered = False
            if p_side == "buy" and current_price >= p_stop:
                stop_triggered = True
            elif p_side == "sell" and current_price <= p_stop:
                stop_triggered = True
            if stop_triggered:
                if p_side == "buy" and current_price <= p_limit:
                    triggered = True
                    filled_price = min(current_price, p_limit)
                elif p_side == "sell" and current_price >= p_limit:
                    triggered = True
                    filled_price = max(current_price, p_limit)

        if not triggered:
            continue

        now = _now_iso()
        try:
            _execute_trade(conn, p_side, p_symbol, p_qty, filled_price, p_fee)
            conn.execute(
                "UPDATE pending_orders SET status = 'filled', filled_price = ?, filled_at = ?, updated_at = ? WHERE id = ?",
                (filled_price, now, now, order_id),
            )
        except ValueError as exc:
            conn.execute(
                "UPDATE pending_orders SET status = 'expired', reject_reason = ?, updated_at = ? WHERE id = ?",
                (str(exc), now, order_id),
            )
            warnings.append(f"pending order #{order_id} ({p_symbol}): expired — {exc}")

    return warnings


def get_pending_orders(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    init_db(db_path)
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM pending_orders WHERE account_id = ? AND status = 'pending' ORDER BY id DESC",
            (DEFAULT_ACCOUNT_ID,),
        ).fetchall()
    return [dict(row) for row in rows]


def cancel_pending_order(order_id: int, db_path: Optional[Path] = None) -> Dict[str, Any]:
    init_db(db_path)
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM pending_orders WHERE id = ? AND account_id = ? AND status = 'pending'",
            (order_id, DEFAULT_ACCOUNT_ID),
        ).fetchone()
        if not row:
            raise ValueError("pending order not found or already executed")
        now = _now_iso()
        conn.execute(
            "UPDATE pending_orders SET status = 'cancelled', updated_at = ? WHERE id = ?",
            (now, order_id),
        )
        conn.commit()
    return {"id": order_id, "status": "cancelled"}


def get_trades(limit: int = 100, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    init_db(db_path)
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM trades WHERE account_id = ? ORDER BY id DESC LIMIT ?",
            (DEFAULT_ACCOUNT_ID, int(limit)),
        ).fetchall()
    return [dict(row) for row in rows]


def get_account_snapshot(db_path: Optional[Path] = None, refresh_prices: bool = True) -> Dict[str, Any]:
    init_db(db_path)
    warnings = ["Virtual trading uses free yfinance quotes and is for product simulation only."]
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    with _connect(db_path) as conn:
        account = _get_account(conn)

        # Process pending orders before reading positions
        if refresh_prices:
            try:
                pending_warnings = _process_pending_orders(conn)
                warnings.extend(pending_warnings)
                conn.commit()
            except Exception:
                pass  # Don't fail snapshot if pending processing errors

        position_rows = conn.execute(
            "SELECT * FROM positions WHERE account_id = ? ORDER BY symbol",
            (DEFAULT_ACCOUNT_ID,),
        ).fetchall()

    positions = []
    holdings_value = 0.0
    unrealized_pnl = 0.0
    today_unrealized = 0.0
    for row in position_rows:
        symbol = row["symbol"]
        quantity = float(row["quantity"])
        average_cost = float(row["average_cost"])
        previous_close = None
        if refresh_prices:
            try:
                quote = _latest_price(symbol)
                latest_price = quote["price"]
                name = quote["name"]
                currency = quote["currency"]
                exchange = quote["exchange"]
                previous_close = quote.get("previousClose") or None
            except Exception as exc:
                latest_price = average_cost
                name = symbol
                currency = "USD"
                exchange = ""
                warnings.append(f"{symbol} latest price unavailable, using average cost. {exc}")
        else:
            latest_price = average_cost
            name = symbol
            currency = "USD"
            exchange = ""

        market_value = quantity * latest_price
        position_unrealized = (latest_price - average_cost) * quantity
        holdings_value += market_value
        unrealized_pnl += position_unrealized
        # Today's unrealized change per position
        if previous_close and previous_close > 0:
            today_unrealized += (latest_price - previous_close) * quantity

        positions.append(
            {
                "symbol": symbol,
                "name": name,
                "quantity": _safe_float(quantity),
                "averageCost": _safe_float(average_cost),
                "latestPrice": _safe_float(latest_price),
                "marketValue": _safe_float(market_value),
                "unrealizedPnl": _safe_float(position_unrealized),
                "unrealizedPnlPercent": _safe_float(position_unrealized / (average_cost * quantity), 6) if average_cost and quantity else None,
                "realizedPnl": _safe_float(row["realized_pnl"]),
                "currency": currency,
                "exchange": exchange,
            }
        )

    # Today's realized PnL from trades executed today
    today_realized = 0.0
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(realized_pnl), 0) FROM trades WHERE account_id = ? AND date(created_at) = ?",
            (DEFAULT_ACCOUNT_ID, today_str),
        ).fetchone()
        today_realized = float(row[0]) if row else 0.0

    cash = float(account["cash"])
    realized = float(account["realized_pnl"])
    total_assets = cash + holdings_value
    cumulative_pnl = total_assets - float(account["initial_cash"])
    today_pnl = today_unrealized + today_realized

    # Record daily snapshot
    with _connect(db_path) as conn:
        now = _now_iso()
        conn.execute(
            """
            INSERT INTO daily_snapshots (account_id, snapshot_date, total_assets, cash, holdings_value, cumulative_pnl, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(account_id, snapshot_date) DO UPDATE SET
                total_assets = excluded.total_assets,
                cash = excluded.cash,
                holdings_value = excluded.holdings_value,
                cumulative_pnl = excluded.cumulative_pnl,
                created_at = excluded.created_at
            """,
            (DEFAULT_ACCOUNT_ID, today_str, total_assets, cash, holdings_value, cumulative_pnl, now),
        )

        # Fetch recent snapshots for sparkline
        snapshots = conn.execute(
            "SELECT snapshot_date, cumulative_pnl FROM daily_snapshots WHERE account_id = ? ORDER BY snapshot_date ASC LIMIT 30",
            (DEFAULT_ACCOUNT_ID,),
        ).fetchall()
        sparkline = [{"date": s["snapshot_date"], "cumulativePnl": _safe_float(s["cumulative_pnl"])} for s in snapshots]
        conn.commit()

    return {
        "account": {
            "id": DEFAULT_ACCOUNT_ID,
            "cash": _safe_float(cash),
            "holdingsValue": _safe_float(holdings_value),
            "totalAssets": _safe_float(total_assets),
            "realizedPnl": _safe_float(realized),
            "unrealizedPnl": _safe_float(unrealized_pnl),
            "cumulativePnl": _safe_float(cumulative_pnl),
            "cumulativePnlPercent": _safe_float(cumulative_pnl / float(account["initial_cash"]), 6),
            "todayPnl": _safe_float(today_pnl),
            "initialCash": _safe_float(account["initial_cash"]),
            "updatedAt": account["updated_at"],
            "sparkline": sparkline,
        },
        "positions": positions,
        "trades": get_trades(limit=50, db_path=db_path),
        "warnings": warnings,
    }


def account_response(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    return success_response(
        snapshot,
        market_meta(warnings=snapshot.get("warnings", [])),
    )



