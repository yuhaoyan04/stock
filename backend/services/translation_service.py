"""Optional translation service for public finance content.

DeepSeek is used only when DEEPSEEK_API_KEY is configured. The rest of the
application should keep working without a translation provider.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import timedelta
from threading import Lock
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from utils.api_response import now_iso, success_response


DEFAULT_MODEL = "deepseek-chat"
DEFAULT_BASE_URL = "https://api.deepseek.com/chat/completions"
MAX_TEXTS = 8
MAX_CHARS_PER_TEXT = 1500

_cache: Dict[str, Dict[str, Any]] = {}
_cache_lock = Lock()


def detect_language(text: str) -> str:
    value = text or ""
    if re.search(r"[\u3040-\u30ff]", value):
        return "ja"
    if re.search(r"[\u4e00-\u9fff]", value):
        return "zh-CN"
    if re.search(r"[A-Za-z]", value):
        return "en"
    return "unknown"


def _cache_key(texts: List[str], target_language: str) -> str:
    raw = json.dumps({"texts": texts, "target": target_language}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _extract_json_array(value: str) -> List[str]:
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
        if isinstance(parsed, dict) and isinstance(parsed.get("translations"), list):
            return [str(item) for item in parsed["translations"]]
    except json.JSONDecodeError:
        pass

    match = re.search(r"\[[\s\S]*\]", value)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            pass
    return []


def _call_deepseek(texts: List[str], target_language: str) -> List[str]:
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not configured")

    model = os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    base_url = os.getenv("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL
    prompt = (
        "Translate the following finance education or macro policy snippets into clear Simplified Chinese. "
        "Every English, Japanese, or other non-Chinese sentence must be rendered in Simplified Chinese; do not copy it verbatim. "
        "If a snippet is already Chinese, return it unchanged. "
        "Keep tickers, institution names, dates, percentages, and URLs unchanged. "
        "Do not add investment advice, explanation, markdown, or extra fields. "
        "Return only a JSON array of translated strings in the same order.\n\n"
        + json.dumps(texts, ensure_ascii=False)
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a precise financial translator."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
    }
    request = Request(
        base_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "StockResearchMVP/1.0",
        },
        method="POST",
    )
    with urlopen(request, timeout=20) as response:  # nosec B310 - user-configured official API endpoint
        body = json.loads(response.read().decode("utf-8"))
    content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    translated = _extract_json_array(content)
    if len(translated) != len(texts):
        raise RuntimeError("Translation provider returned an unexpected response")
    return translated


def translate_texts(texts: List[str], target_language: str = "zh-CN") -> Dict[str, Any]:
    clean_texts = [" ".join((text or "").split())[:MAX_CHARS_PER_TEXT] for text in texts]
    clean_texts = [text for text in clean_texts if text]
    if not clean_texts:
        return success_response(
            {"available": False, "translations": []},
            {"source": "translation", "last_updated": now_iso(), "warnings": ["没有可翻译文本。"]},
        )
    if len(clean_texts) > MAX_TEXTS:
        clean_texts = clean_texts[:MAX_TEXTS]

    key = _cache_key(clean_texts, target_language)
    with _cache_lock:
        cached = _cache.get(key)
        if cached:
            return cached

    if not os.getenv("DEEPSEEK_API_KEY", "").strip():
        payload = success_response(
            {"available": False, "translations": clean_texts},
            {
                "source": "DeepSeek",
                "last_updated": now_iso(),
                "timezone": "UTC",
                "adjusted": False,
                "delayed": False,
                "warnings": ["未配置 DEEPSEEK_API_KEY，已保留原文。"],
            },
        )
        return payload

    try:
        translated = _call_deepseek(clean_texts, target_language)
    except (HTTPError, URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"翻译服务暂时不可用：{exc}") from exc

    payload = success_response(
        {"available": True, "translations": translated},
        {
            "source": "DeepSeek",
            "last_updated": now_iso(),
            "timezone": "UTC",
            "adjusted": False,
            "delayed": False,
            "warnings": [],
        },
    )
    with _cache_lock:
        if len(_cache) > 200:
            _cache.clear()
        _cache[key] = payload
    return payload
