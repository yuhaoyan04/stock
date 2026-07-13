"""
Yahoo Finance 数据服务封装层
使用 yfinance 库获取股票、ETF、指数、期货、外汇、加密货币数据
"""
import yfinance as yf
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
from difflib import SequenceMatcher


# ── 常用资产分类 ───────────────────────────────────────────
POPULAR_SYMBOLS = {
    "indices": [
        {"symbol": "^GSPC", "name": "S&P 500", "type": "index"},
        {"symbol": "^NDX", "name": "NASDAQ 100", "type": "index"},
        {"symbol": "^DJI", "name": "Dow Jones", "type": "index"},
        {"symbol": "^RUT", "name": "Russell 2000", "type": "index"},
        {"symbol": "^VIX", "name": "VIX Volatility", "type": "index"},
        {"symbol": "^HSI", "name": "Hang Seng", "type": "index"},
        {"symbol": "^N225", "name": "Nikkei 225", "type": "index"},
        {"symbol": "^FTSE", "name": "FTSE 100", "type": "index"},
    ],
    "etfs": [
        {"symbol": "SPY", "name": "SPDR S&P 500 ETF", "type": "etf"},
        {"symbol": "QQQ", "name": "Invesco QQQ Trust", "type": "etf"},
        {"symbol": "IWM", "name": "iShares Russell 2000", "type": "etf"},
        {"symbol": "DIA", "name": "SPDR Dow Jones", "type": "etf"},
        {"symbol": "VTI", "name": "Vanguard Total Stock Market", "type": "etf"},
        {"symbol": "VOO", "name": "Vanguard S&P 500", "type": "etf"},
        {"symbol": "XLF", "name": "Financial Select Sector", "type": "etf"},
        {"symbol": "XLK", "name": "Technology Select Sector", "type": "etf"},
        {"symbol": "XLE", "name": "Energy Select Sector", "type": "etf"},
        {"symbol": "GLD", "name": "SPDR Gold Trust", "type": "etf"},
        {"symbol": "TLT", "name": "iShares 20+ Year Treasury", "type": "etf"},
        {"symbol": "ARKK", "name": "ARK Innovation ETF", "type": "etf"},
    ],
    "futures": [
        {"symbol": "ES=F", "name": "E-mini S&P 500 Futures", "type": "future"},
        {"symbol": "NQ=F", "name": "E-mini NASDAQ 100 Futures", "type": "future"},
        {"symbol": "YM=F", "name": "E-mini Dow Futures", "type": "future"},
        {"symbol": "RTY=F", "name": "E-mini Russell 2000 Futures", "type": "future"},
        {"symbol": "CL=F", "name": "Crude Oil Futures", "type": "future"},
        {"symbol": "GC=F", "name": "Gold Futures", "type": "future"},
        {"symbol": "SI=F", "name": "Silver Futures", "type": "future"},
        {"symbol": "NG=F", "name": "Natural Gas Futures", "type": "future"},
        {"symbol": "ZC=F", "name": "Corn Futures", "type": "future"},
        {"symbol": "ZS=F", "name": "Soybean Futures", "type": "future"},
    ],
    "forex": [
        {"symbol": "EURUSD=X", "name": "Euro / US Dollar", "type": "forex"},
        {"symbol": "USDJPY=X", "name": "US Dollar / Japanese Yen", "type": "forex"},
        {"symbol": "GBPUSD=X", "name": "British Pound / US Dollar", "type": "forex"},
        {"symbol": "USDCNY=X", "name": "US Dollar / Chinese Yuan", "type": "forex"},
        {"symbol": "AUDUSD=X", "name": "Australian Dollar / US Dollar", "type": "forex"},
        {"symbol": "USDCAD=X", "name": "US Dollar / Canadian Dollar", "type": "forex"},
        {"symbol": "USDCHF=X", "name": "US Dollar / Swiss Franc", "type": "forex"},
    ],
    "crypto": [
        {"symbol": "BTC-USD", "name": "Bitcoin USD", "type": "crypto"},
        {"symbol": "ETH-USD", "name": "Ethereum USD", "type": "crypto"},
        {"symbol": "SOL-USD", "name": "Solana USD", "type": "crypto"},
        {"symbol": "DOGE-USD", "name": "Dogecoin USD", "type": "crypto"},
        {"symbol": "ADA-USD", "name": "Cardano USD", "type": "crypto"},
    ],
    "popular_stocks": [
        {"symbol": "AAPL", "name": "Apple Inc.", "type": "stock", "sector": "Technology"},
        {"symbol": "MSFT", "name": "Microsoft Corp.", "type": "stock", "sector": "Technology"},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "type": "stock", "sector": "Technology"},
        {"symbol": "AMZN", "name": "Amazon.com Inc.", "type": "stock", "sector": "Consumer Cyclical"},
        {"symbol": "NVDA", "name": "NVIDIA Corp.", "type": "stock", "sector": "Technology"},
        {"symbol": "META", "name": "Meta Platforms Inc.", "type": "stock", "sector": "Technology"},
        {"symbol": "TSLA", "name": "Tesla Inc.", "type": "stock", "sector": "Consumer Cyclical"},
        {"symbol": "BRK-B", "name": "Berkshire Hathaway", "type": "stock", "sector": "Financial"},
        {"symbol": "JPM", "name": "JPMorgan Chase", "type": "stock", "sector": "Financial"},
        {"symbol": "V", "name": "Visa Inc.", "type": "stock", "sector": "Financial"},
        {"symbol": "JNJ", "name": "Johnson & Johnson", "type": "stock", "sector": "Healthcare"},
        {"symbol": "WMT", "name": "Walmart Inc.", "type": "stock", "sector": "Consumer Defensive"},
        {"symbol": "PG", "name": "Procter & Gamble", "type": "stock", "sector": "Consumer Defensive"},
        {"symbol": "XOM", "name": "Exxon Mobil", "type": "stock", "sector": "Energy"},
        {"symbol": "UNH", "name": "UnitedHealth Group", "type": "stock", "sector": "Healthcare"},
        {"symbol": "HD", "name": "Home Depot", "type": "stock", "sector": "Consumer Cyclical"},
        {"symbol": "BAC", "name": "Bank of America", "type": "stock", "sector": "Financial"},
        {"symbol": "DIS", "name": "Walt Disney Co.", "type": "stock", "sector": "Communication"},
        {"symbol": "NFLX", "name": "Netflix Inc.", "type": "stock", "sector": "Communication"},
        {"symbol": "ADBE", "name": "Adobe Inc.", "type": "stock", "sector": "Technology"},
    ],
}

# A small, stable alias catalog keeps the core search experience usable when
# Yahoo's remote search endpoint is slow or unavailable.  These are display
# aliases, not translated company names sourced from a live provider.
LOCALIZED_ALIASES = {
    "AAPL": ["苹果", "苹果公司", "Apple", "Apple Inc"],
    "MSFT": ["微软", "微软公司", "Microsoft"],
    "GOOGL": ["谷歌", "Google", "Alphabet", "字母表公司"],
    "AMZN": ["亚马逊", "亚马逊公司", "Amazon"],
    "NVDA": ["英伟达", "英伟达公司", "NVIDIA", "黄仁勋公司"],
    "META": ["脸书", "Meta", "Facebook", "元平台"],
    "TSLA": ["特斯拉", "特斯拉汽车", "Tesla"],
    "BRK-B": ["伯克希尔", "伯克希尔哈撒韦", "巴菲特公司", "Berkshire"],
    "JPM": ["摩根大通", "JPMorgan"],
    "V": ["Visa", "维萨"],
    "JNJ": ["强生", "Johnson & Johnson"],
    "WMT": ["沃尔玛", "Walmart"],
    "PG": ["宝洁", "Procter Gamble"],
    "XOM": ["埃克森美孚", "美孚", "Exxon"],
    "DIS": ["迪士尼", "Disney"],
    "NFLX": ["奈飞", "网飞", "Netflix"],
    "SPY": ["标普500", "标普", "S&P 500", "标普500ETF"],
    "QQQ": ["纳斯达克100", "纳指100", "纳斯达克ETF"],
    "DIA": ["道琼斯", "道指"],
    "IWM": ["罗素2000", "罗素ETF"],
    "GLD": ["黄金", "黄金ETF"],
    "CL=F": ["原油", "石油", "WTI", "原油期货"],
    "GC=F": ["黄金期货", "金价"],
    "BTC-USD": ["比特币", "BTC", "Bitcoin"],
    "ETH-USD": ["以太坊", "ETH", "Ethereum"],
}

POPULARITY_RANK = {
    symbol: index
    for index, symbol in enumerate(
        ["AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "GOOGL", "META", "SPY", "QQQ", "BTC-USD", "GLD", "CL=F"],
        start=1,
    )
}


def _safe_value(val):
    """将 numpy/NaN 转为 Python 原生类型"""
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    try:
        if hasattr(val, "item"):
            return val.item()
    except (TypeError, ValueError):
        pass
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.isoformat()
    return val


def _dict_to_native(d: Dict) -> Dict:
    """递归转换字典中的值"""
    result = {}
    for k, v in d.items():
        if isinstance(v, dict):
            result[k] = _dict_to_native(v)
        elif isinstance(v, list):
            result[k] = [_safe_value(x) for x in v]
        else:
            result[k] = _safe_value(v)
    return result


# ── 搜索 ────────────────────────────────────────────────────

def search_symbols(query: str, limit: int = 15) -> List[Dict]:
    """搜索股票代码、英文名、中文别名，并用简单相似度改善模糊匹配。"""
    query_text = str(query or "").strip()
    query_lower = query_text.lower()
    catalog = {}
    for category in POPULAR_SYMBOLS.values():
        for item in category:
            catalog.setdefault(item["symbol"], item)

    def enrich(item: Dict[str, Any], score: float = 0, popular: bool = False) -> Dict[str, Any]:
        result = dict(item)
        aliases = LOCALIZED_ALIASES.get(result["symbol"], [])
        result["aliases"] = aliases
        result["searchLabel"] = " / ".join([result.get("name", ""), *aliases])
        result["popularityRank"] = POPULARITY_RANK.get(result["symbol"])
        result["isPopular"] = popular or result["symbol"] in POPULARITY_RANK
        result["matchScore"] = round(score, 4)
        return result

    if not query_text:
        featured = sorted(
            catalog.values(),
            key=lambda item: POPULARITY_RANK.get(item["symbol"], 999),
        )
        return [enrich(item, 1, True) for item in featured[:limit]]

    scored = []
    for item in catalog.values():
        symbol = item["symbol"].lower()
        name = item.get("name", "").lower()
        aliases = [str(alias).lower() for alias in LOCALIZED_ALIASES.get(item["symbol"], [])]
        fields = [symbol, name, *aliases]
        if query_lower == symbol:
            score = 1.0
        elif any(query_lower == alias for alias in aliases):
            score = 0.99
        elif any(query_lower in field for field in fields):
            score = 0.9
        else:
            score = max((SequenceMatcher(None, query_lower, field).ratio() for field in fields), default=0)
        if score >= 0.42:
            scored.append((score, item))

    scored.sort(key=lambda row: (-row[0], POPULARITY_RANK.get(row[1]["symbol"], 999)))
    results = [enrich(item, score) for score, item in scored[:limit]]

    # 如果本地结果不足，尝试 Yahoo Finance 搜索
    if len(results) < limit and query_text.isascii():
        try:
            ticker = yf.Ticker(query_text.upper())
            info = ticker.info
            if info and info.get("symbol"):
                local_symbols = {r["symbol"] for r in results}
                if info["symbol"] not in local_symbols:
                    sector = info.get("sector", "") or info.get("industry", "") or ""
                    results.append(
                        {
                            "symbol": info["symbol"],
                            "name": info.get("longName") or info.get("shortName", query_text.upper()),
                            "type": info.get("quoteType", "stock"),
                            "exchange": info.get("exchange", ""),
                            "sector": sector,
                        }
                    )
        except Exception:
            pass

    return results[:limit]


# ── 公司/资产信息 ───────────────────────────────────────────

def get_stock_info(symbol: str) -> Dict[str, Any]:
    """获取股票/资产的详细信息"""
    ticker = yf.Ticker(symbol)
    info = ticker.info

    result = {
        "symbol": info.get("symbol", symbol),
        "name": info.get("longName") or info.get("shortName", ""),
        "type": info.get("quoteType", ""),
        "exchange": info.get("exchange", ""),
        "currency": info.get("currency", "USD"),
        "sector": info.get("sector", ""),
        "industry": info.get("industry", ""),
        "website": info.get("website", ""),
        "description": info.get("longBusinessSummary", ""),
        "country": info.get("country", ""),
        "employees": _safe_value(info.get("fullTimeEmployees")),
        # 价格
        "currentPrice": _safe_value(info.get("currentPrice") or info.get("regularMarketPrice")),
        "previousClose": _safe_value(info.get("previousClose") or info.get("regularMarketPreviousClose")),
        "open": _safe_value(info.get("open") or info.get("regularMarketOpen")),
        "dayHigh": _safe_value(info.get("dayHigh") or info.get("regularMarketDayHigh")),
        "dayLow": _safe_value(info.get("dayLow") or info.get("regularMarketDayLow")),
        "volume": _safe_value(info.get("volume") or info.get("regularMarketVolume")),
        "avgVolume": _safe_value(info.get("averageVolume")),
        "fiftyTwoWeekHigh": _safe_value(info.get("fiftyTwoWeekHigh")),
        "fiftyTwoWeekLow": _safe_value(info.get("fiftyTwoWeekLow")),
        # 估值
        "marketCap": _safe_value(info.get("marketCap")),
        "enterpriseValue": _safe_value(info.get("enterpriseValue")),
        "peRatio": _safe_value(info.get("trailingPE") or info.get("forwardPE")),
        "forwardPE": _safe_value(info.get("forwardPE")),
        "pegRatio": _safe_value(info.get("pegRatio")),
        "priceToBook": _safe_value(info.get("priceToBook")),
        "priceToSales": _safe_value(info.get("priceToSales")),
        # 盈利能力
        "eps": _safe_value(info.get("trailingEps")),
        "forwardEps": _safe_value(info.get("forwardEps")),
        "revenuePerShare": _safe_value(info.get("revenuePerShare")),
        "returnOnEquity": _safe_value(info.get("returnOnEquity")),
        # 分红
        "dividendRate": _safe_value(info.get("dividendRate")),
        "dividendYield": _safe_value(info.get("dividendYield")),
        "payoutRatio": _safe_value(info.get("payoutRatio")),
        # 风险指标
        "beta": _safe_value(info.get("beta")),
        # 目标价
        "targetMeanPrice": _safe_value(info.get("targetMeanPrice")),
        "targetHighPrice": _safe_value(info.get("targetHighPrice")),
        "targetLowPrice": _safe_value(info.get("targetLowPrice")),
        "recommendationMean": _safe_value(info.get("recommendationMean")),
        "numberOfAnalystOpinions": _safe_value(info.get("numberOfAnalystOpinions")),
    }
    return _dict_to_native(result)


# ── 历史K线数据 ─────────────────────────────────────────────

def get_stock_history(
    symbol: str,
    period: str = "1mo",
    interval: str = "1d",
) -> List[Dict]:
    """
    获取历史K线数据
    period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    """
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)

    if df.empty:
        return []

    records = []
    for idx, row in df.iterrows():
        record = {
            "date": idx.isoformat() if hasattr(idx, "isoformat") else str(idx),
            "open": _safe_value(row.get("Open")),
            "high": _safe_value(row.get("High")),
            "low": _safe_value(row.get("Low")),
            "close": _safe_value(row.get("Close")),
            "volume": _safe_value(row.get("Volume")),
        }
        records.append(record)
    return records


# ── 财务报表 ────────────────────────────────────────────────

def get_financials(symbol: str, statement_type: str = "income", period: str = "annual") -> List[Dict]:
    """
    获取财务报表
    statement_type: income | balance | cashflow
    period: annual | quarterly
    """
    ticker = yf.Ticker(symbol)

    if statement_type == "income":
        df = ticker.financials if period == "annual" else ticker.quarterly_financials
    elif statement_type == "balance":
        df = ticker.balance_sheet if period == "annual" else ticker.quarterly_balance_sheet
    elif statement_type == "cashflow":
        df = ticker.cashflow if period == "annual" else ticker.quarterly_cashflow
    else:
        return []

    if df is None or df.empty:
        return []

    # 转置，使日期为行
    df = df.T
    records = []
    for idx, row in df.iterrows():
        record = {"date": idx.isoformat() if hasattr(idx, "isoformat") else str(idx)}
        for col in df.columns:
            record[col] = _safe_value(row[col])
        records.append(record)

    return records


# ── 市场总览 ────────────────────────────────────────────────

def get_market_overview() -> Dict[str, Any]:
    """获取市场总览 — 各指数/板块表现"""
    indices = [
        {"symbol": "SPY", "name": "S&P 500 ETF", "type": "etf"},
        {"symbol": "QQQ", "name": "NASDAQ 100 ETF", "type": "etf"},
        {"symbol": "DIA", "name": "Dow Jones ETF", "type": "etf"},
        {"symbol": "IWM", "name": "Russell 2000 ETF", "type": "etf"},
        {"symbol": "^VIX", "name": "VIX Volatility", "type": "index"},
        {"symbol": "^TNX", "name": "10Y Treasury Yield", "type": "index"},
        {"symbol": "DX-Y.NYB", "name": "US Dollar Index", "type": "index"},
        {"symbol": "GC=F", "name": "Gold Futures", "type": "future"},
        {"symbol": "CL=F", "name": "Crude Oil Futures", "type": "future"},
        {"symbol": "BTC-USD", "name": "Bitcoin", "type": "crypto"},
    ]
    index_data = []

    for idx in indices:
        try:
            ticker = yf.Ticker(idx["symbol"])
            info = ticker.info
            hist = ticker.history(period="5d")

            price = _safe_value(info.get("regularMarketPrice") or info.get("currentPrice"))
            prev_close = _safe_value(info.get("regularMarketPreviousClose") or info.get("previousClose"))
            change = None
            change_pct = None
            if price is not None and prev_close is not None and prev_close != 0:
                change = round(price - prev_close, 2)
                change_pct = round((change / prev_close) * 100, 2)

            # 5日迷你走势
            mini_chart = []
            if not hist.empty:
                for dt, row in hist.iterrows():
                    mini_chart.append(_safe_value(row.get("Close")))

            index_data.append(
                {
                    "symbol": idx["symbol"],
                    "name": idx["name"],
                    "price": price,
                    "change": change,
                    "changePercent": change_pct,
                    "miniChart": mini_chart,
                }
            )
        except Exception:
            index_data.append(
                {
                    "symbol": idx["symbol"],
                    "name": idx["name"],
                    "price": None,
                    "change": None,
                    "changePercent": None,
                    "miniChart": [],
                }
            )

    # 热门股票概览
    stocks = POPULAR_SYMBOLS["popular_stocks"][:10]
    stock_data = []
    for s in stocks:
        try:
            ticker = yf.Ticker(s["symbol"])
            info = ticker.info
            hist = ticker.history(period="5d")
            price = _safe_value(info.get("regularMarketPrice") or info.get("currentPrice"))
            prev_close = _safe_value(info.get("regularMarketPreviousClose") or info.get("previousClose"))
            change = None
            change_pct = None
            if price is not None and prev_close is not None and prev_close != 0:
                change = round(price - prev_close, 2)
                change_pct = round((change / prev_close) * 100, 2)

            mini_chart = []
            if not hist.empty:
                for dt, row in hist.iterrows():
                    mini_chart.append(_safe_value(row.get("Close")))

            stock_data.append(
                {
                    "symbol": s["symbol"],
                    "name": s["name"],
                    "sector": s.get("sector", ""),
                    "price": price,
                    "change": change,
                    "changePercent": change_pct,
                    "marketCap": _safe_value(info.get("marketCap")),
                    "miniChart": mini_chart,
                }
            )
        except Exception:
            stock_data.append(
                {
                    "symbol": s["symbol"],
                    "name": s["name"],
                    "sector": s.get("sector", ""),
                    "price": None,
                    "change": None,
                    "changePercent": None,
                    "marketCap": None,
                    "miniChart": [],
                }
            )

    return {
        "indices": index_data,
        "hotStocks": stock_data,
        "fetchedAt": datetime.now().isoformat(),
    }


# ── 多资产对比 ──────────────────────────────────────────────

def compare_symbols(symbols: List[str], period: str = "1y") -> Dict[str, Any]:
    """
    多资产对比 — 返回百分比归化的走势数据
    """
    series = {}
    dates = []

    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period)

            if df.empty:
                series[symbol] = []
                continue

            closes = df["Close"].tolist()
            base = closes[0] if closes else 1
            if base == 0:
                base = 1

            # 百分比归化（以起始日为 100%）
            normalized = [round((c / base) * 100, 2) for c in closes]
            series[symbol] = normalized

            if not dates:
                dates = [
                    idx.isoformat() if hasattr(idx, "isoformat") else str(idx)
                    for idx in df.index
                ]
        except Exception:
            series[symbol] = []

    return {"dates": dates, "series": series}


# ── 热门分类列表 ────────────────────────────────────────────

def get_category_symbols() -> Dict[str, List[Dict]]:
    """返回所有预置的分类和标的"""
    return POPULAR_SYMBOLS

