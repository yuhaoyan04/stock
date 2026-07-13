"""Small helpers for consistent API responses."""
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def market_meta(**overrides: Any) -> Dict[str, Any]:
    meta = {
        "source": "yfinance",
        "last_updated": now_iso(),
        "timezone": "America/New_York",
        "adjusted": True,
        "delayed": True,
        "warnings": [],
    }
    meta.update({key: value for key, value in overrides.items() if value is not None})
    return meta


def success_response(data: Any, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "success": True,
        "data": data,
        "meta": meta or market_meta(),
        "error": None,
    }


def error_response(code: str, message: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "success": False,
        "data": None,
        "meta": meta or {},
        "error": {
            "code": code,
            "message": message,
        },
    }
