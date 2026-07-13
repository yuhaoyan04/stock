"""组合回测与基础权重优化服务"""
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import yfinance as yf

from utils.api_response import market_meta, success_response


TRADING_DAYS = 252
MIN_OBSERVATIONS = 20


def _safe_float(value, digits: Optional[int] = None):
    if value is None:
        return None
    try:
        if pd.isna(value) or np.isinf(value):
            return None
    except TypeError:
        pass
    result = float(value)
    return round(result, digits) if digits is not None else result


def _clean_symbols(symbols: List[str]) -> List[str]:
    clean_symbols = []
    for symbol in symbols:
        normalized = str(symbol).strip().upper()
        if normalized and normalized not in clean_symbols:
            clean_symbols.append(normalized)
    return clean_symbols


def _normalize_weights(symbols: List[str], weights: Optional[Dict[str, float]]) -> Dict[str, float]:
    if not weights:
        equal = 1 / len(symbols)
        return {symbol: equal for symbol in symbols}

    normalized = {symbol: float(weights.get(symbol, 0)) for symbol in symbols}
    total = sum(normalized.values())
    if total <= 0:
        raise ValueError("custom weights must sum to 100%")
    return {symbol: weight / total for symbol, weight in normalized.items()}


def _validate_custom_weights(symbols: List[str], weights: Optional[Dict[str, float]]) -> Dict[str, float]:
    if not weights:
        raise ValueError("custom mode requires weights for every symbol")

    normalized_input = {str(key).strip().upper(): value for key, value in weights.items()}
    missing = [symbol for symbol in symbols if symbol not in normalized_input]
    if missing:
        raise ValueError(f"missing custom weights for: {', '.join(missing)}")

    values: Dict[str, float] = {}
    for symbol in symbols:
        try:
            value = float(normalized_input[symbol])
        except (TypeError, ValueError):
            raise ValueError(f"weight for {symbol} must be a number")
        if value < 0:
            raise ValueError("weights cannot be negative")
        values[symbol] = value

    total = sum(values.values())
    if abs(total - 100) > 0.5:
        raise ValueError(f"custom weights must sum to 100%, current total is {total:.2f}%")

    return {symbol: value / 100 for symbol, value in values.items()}


def _load_prices(symbols: List[str], period: str) -> pd.DataFrame:
    frames = []
    for symbol in symbols:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period, interval="1d", auto_adjust=True)
        if history.empty or "Close" not in history:
            continue
        series = history["Close"].rename(symbol)
        frames.append(series)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, axis=1).dropna(how="any")


def _portfolio_metrics(portfolio_returns: pd.Series) -> Dict[str, Any]:
    if portfolio_returns.empty:
        return {
            "totalReturn": None,
            "annualReturn": None,
            "annualVolatility": None,
            "sharpeRatio": None,
            "maxDrawdown": None,
            "bestDay": None,
            "worstDay": None,
            "positiveDays": None,
        }

    equity = (1 + portfolio_returns).cumprod()
    total_return = equity.iloc[-1] - 1
    years = max(len(portfolio_returns) / TRADING_DAYS, 1 / TRADING_DAYS)
    annual_return = (1 + total_return) ** (1 / years) - 1
    annual_vol = portfolio_returns.std() * np.sqrt(TRADING_DAYS)
    sharpe = annual_return / annual_vol if annual_vol and annual_vol > 0 else None
    drawdown = equity / equity.cummax() - 1
    positive_days = (portfolio_returns > 0).mean()

    return {
        "totalReturn": _safe_float(total_return, 4),
        "annualReturn": _safe_float(annual_return, 4),
        "annualVolatility": _safe_float(annual_vol, 4),
        "sharpeRatio": _safe_float(sharpe, 3),
        "maxDrawdown": _safe_float(drawdown.min(), 4),
        "bestDay": _safe_float(portfolio_returns.max(), 4),
        "worstDay": _safe_float(portfolio_returns.min(), 4),
        "positiveDays": _safe_float(positive_days, 4),
    }


def _optimize_weights(returns: pd.DataFrame, mode: str, custom_weights: Dict[str, float]) -> Dict[str, float]:
    symbols = list(returns.columns)

    if mode == "custom":
        return _normalize_weights(symbols, custom_weights)

    if mode == "equal":
        return _normalize_weights(symbols, None)

    if mode == "risk_parity":
        vol = returns.std().replace(0, np.nan)
        inv_vol = (1 / vol).replace([np.inf, -np.inf], np.nan).fillna(0)
        total = inv_vol.sum()
        if total <= 0:
            return _normalize_weights(symbols, None)
        return {symbol: float(inv_vol[symbol] / total) for symbol in symbols}

    if len(symbols) == 1:
        return {symbols[0]: 1.0}

    mean_returns = returns.mean() * TRADING_DAYS
    covariance = returns.cov() * TRADING_DAYS
    rng = np.random.default_rng(42)
    best_weights = None
    best_score = None

    for _ in range(6000):
        candidate = rng.random(len(symbols))
        candidate = candidate / candidate.sum()
        expected_return = float(np.dot(candidate, mean_returns))
        volatility = float(np.sqrt(np.dot(candidate.T, np.dot(covariance, candidate))))
        sharpe = expected_return / volatility if volatility > 0 else -np.inf

        score = volatility if mode == "min_variance" else -sharpe
        if best_score is None or score < best_score:
            best_score = score
            best_weights = candidate

    if best_weights is None:
        return _normalize_weights(symbols, None)

    return {symbol: float(best_weights[i]) for i, symbol in enumerate(symbols)}


def _optimization_label(mode: str) -> str:
    return {
        "equal": "等权基线",
        "custom": "用户自定义权重",
        "risk_parity": "按历史波动率反比分配",
        "min_variance": "样本内最小方差",
        "max_sharpe": "样本内最大夏普",
    }.get(mode, mode)


def compare_benchmark(benchmark: str, period: str, target_index: pd.Index) -> Dict[str, Any]:
    if not benchmark:
        return {"symbol": "", "equity": [], "metrics": {}}

    prices = _load_prices([benchmark.strip().upper()], period)
    if prices.empty:
        return {"symbol": benchmark, "equity": [], "metrics": {}}

    returns = prices.pct_change().dropna()
    returns = returns.reindex(target_index).dropna()
    if returns.empty:
        return {"symbol": benchmark, "equity": [], "metrics": {}}

    series = returns.iloc[:, 0]
    equity = (1 + series).cumprod()
    return {
        "symbol": benchmark.strip().upper(),
        "equity": [_safe_float(value, 4) for value in equity.tolist()],
        "dates": [idx.isoformat() if hasattr(idx, "isoformat") else str(idx) for idx in returns.index],
        "metrics": _portfolio_metrics(series),
    }


def backtest_portfolio(
    symbols: List[str],
    period: str = "1y",
    mode: str = "equal",
    weights: Optional[Dict[str, float]] = None,
    benchmark: str = "SPY",
) -> Dict[str, Any]:
    clean_symbols = _clean_symbols(symbols)
    if not clean_symbols:
        raise ValueError("symbols cannot be empty")

    custom_weight_fractions = None
    if mode == "custom":
        custom_weight_fractions = _validate_custom_weights(clean_symbols, weights)

    prices = _load_prices(clean_symbols, period)
    if prices.empty:
        raise ValueError("No price data found for the requested symbols")

    missing_symbols = [symbol for symbol in clean_symbols if symbol not in prices.columns]
    returns = prices.pct_change().dropna(how="any")
    if len(returns) < MIN_OBSERVATIONS:
        raise ValueError("Not enough history to run a reliable backtest")

    active_symbols = list(returns.columns)
    final_weights = _optimize_weights(returns, mode, custom_weight_fractions or {})
    weight_vector = np.array([final_weights[symbol] for symbol in active_symbols])
    portfolio_returns = returns.dot(weight_vector)
    equity = (1 + portfolio_returns).cumprod()
    drawdown = equity / equity.cummax() - 1
    benchmark_data = compare_benchmark(benchmark, period, returns.index)
    benchmark_prices = _load_prices([benchmark.strip().upper()], period) if benchmark else pd.DataFrame()
    benchmark_returns = pd.Series(dtype=float)
    if not benchmark_prices.empty:
        benchmark_returns = benchmark_prices.pct_change().dropna().iloc[:, 0].reindex(returns.index).dropna()
    aligned_portfolio, aligned_benchmark = portfolio_returns.align(benchmark_returns, join="inner")
    fit_coefficient = aligned_portfolio.corr(aligned_benchmark) if len(aligned_portfolio) >= 2 else None

    warnings = [
        "Backtest uses adjusted daily close from yfinance and is for research only.",
        "No financing, taxes, slippage, or intraday execution assumptions are modeled.",
    ]
    if missing_symbols:
        warnings.append(f"Missing price history for: {', '.join(missing_symbols)}")

    data = {
        "symbols": active_symbols,
        "period": period,
        "mode": mode,
        "benchmark": benchmark,
        "allocation": [
            {"symbol": symbol, "weight": _safe_float(final_weights[symbol], 4)}
            for symbol in active_symbols
        ],
        "metrics": {
            **_portfolio_metrics(portfolio_returns),
            "fitCoefficient": _safe_float(fit_coefficient, 4),
            "fitR2": _safe_float(fit_coefficient ** 2 if fit_coefficient is not None else None, 4),
        },
        "dates": [idx.isoformat() if hasattr(idx, "isoformat") else str(idx) for idx in returns.index],
        "equity": [_safe_float(value, 4) for value in equity.tolist()],
        "drawdown": [_safe_float(value, 4) for value in drawdown.tolist()],
        "assetReturns": {
            symbol: [_safe_float(value, 4) for value in returns[symbol].tolist()]
            for symbol in active_symbols
        },
        "benchmarkSeries": benchmark_data,
        "optimization": {
            "label": _optimization_label(mode),
            "method": mode,
            "sampleSize": int(len(returns)),
            "isInSample": mode in {"min_variance", "max_sharpe"},
            "fitCoefficientDefinition": "组合日收益与基准日收益的样本相关系数",
        },
        "assumptions": {
            "price": "adjusted close",
            "rebalance": "buy-and-hold weights over selected window",
            "transactionCost": 0,
            "initialCapital": 100000,
        },
        "dataRange": {
            "start": returns.index[0].isoformat() if hasattr(returns.index[0], "isoformat") else str(returns.index[0]),
            "end": returns.index[-1].isoformat() if hasattr(returns.index[-1], "isoformat") else str(returns.index[-1]),
            "observations": int(len(returns)),
        },
    }

    return success_response(data, market_meta(warnings=warnings))
