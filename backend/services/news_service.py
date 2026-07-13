"""Public macro and policy news aggregation with safe fallbacks.

The app only presents headlines, short source summaries and outbound links.  It
does not republish paywalled or licensed news articles.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
from threading import Lock
from typing import Any, Dict, List
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from xml.etree import ElementTree as ET

from services.translation_service import detect_language
from utils.api_response import now_iso, success_response


CACHE_TTL = timedelta(minutes=15)
_cache: Dict[str, Any] = {"expires_at": datetime.min.replace(tzinfo=timezone.utc), "payload": None}
_cache_lock = Lock()


class _HtmlTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: List[str] = []

    def handle_data(self, data: str):
        self.parts.append(data)


def _plain_text(value: str) -> str:
    """Convert publisher RSS HTML fragments into safe, compact display text."""
    if not value:
        return ""
    parser = _HtmlTextExtractor()
    parser.feed(value)
    parser.close()
    return " ".join(unescape(" ".join(parser.parts)).split())

RSS_SOURCES = [
    {
        "id": "fed",
        "name": "Federal Reserve",
        "url": "https://www.federalreserve.gov/feeds/press_all.xml",
        "topic": "货币政策",
        "description": "美国联邦储备委员会公开发布",
    },
    {
        "id": "imf",
        "name": "IMF",
        "url": "https://www.imf.org/external/rss/feeds.aspx?category=News",
        "urls": ["https://www.imf.org/external/rss/feeds.aspx?category=News", "https://www.imf.org/en/News/RSS"],
        "topic": "全球宏观",
        "description": "国际货币基金组织公开发布",
    },
    {
        "id": "world_bank",
        "name": "World Bank Blogs",
        "url": "https://blogs.worldbank.org/en/rss.xml",
        "urls": ["https://blogs.worldbank.org/en/rss.xml", "https://www.worldbank.org/en/news/all?format=rss"],
        "topic": "政策与发展",
        "description": "世界银行公开博客",
    },
    {"id": "us_media", "name": "Google News · 美国", "url": "https://news.google.com/rss/search?q=monetary+policy+OR+inflation+OR+trade+policy&hl=en-US&gl=US&ceid=US:en", "topic": "美国市场", "region": "美国", "description": "美国主流媒体公开新闻索引"},
    {"id": "europe_media", "name": "Google News · 欧洲", "url": "https://news.google.com/rss/search?q=ECB+OR+inflation+OR+trade+policy&hl=en-GB&gl=GB&ceid=GB:en", "topic": "欧洲市场", "region": "欧洲", "description": "欧洲主流媒体公开新闻索引"},
    {"id": "japan_media", "name": "Google News · 日本", "url": "https://news.google.com/rss/search?q=%E6%97%A5%E9%8A%80+OR+%E7%89%A9%E4%BE%A1+OR+%E8%B2%BF%E6%98%93&hl=ja&gl=JP&ceid=JP:ja", "topic": "日本市场", "region": "日本", "description": "日本主流媒体公开新闻索引"},
    {"id": "singapore_media", "name": "Google News · 新加坡", "url": "https://news.google.com/rss/search?q=MAS+OR+Singapore+economy+OR+trade&hl=en-SG&gl=SG&ceid=SG:en", "topic": "新加坡市场", "region": "新加坡", "description": "新加坡主流媒体公开新闻索引"},
    {"id": "hong_kong", "name": "Hong Kong Government News", "url": "https://www.news.gov.hk/en/categories/finance/html/articlelist.rss.xml", "topic": "香港市场", "region": "香港", "description": "香港政府财经公开发布"},
    {
        "id": "ecb",
        "name": "ECB",
        "url": "https://www.ecb.europa.eu/rss/press.html",
        "topic": "货币政策",
        "region": "欧元区",
        "description": "欧洲央行公开发布",
    },
    {
        "id": "bis",
        "name": "BIS",
        "url": "https://www.bis.org/press/press.rss",
        "urls": ["https://www.bis.org/press/press.rss", "https://www.bis.org/rss/press.rss"],
        "topic": "全球宏观",
        "region": "全球",
        "description": "国际清算银行公开发布",
    },
    {
        "id": "sec",
        "name": "SEC",
        "url": "https://www.sec.gov/news/pressreleases.rss",
        "topic": "监管动态",
        "region": "美国",
        "description": "美国证券交易委员会公开发布",
    },
    {
        "id": "boe",
        "name": "Bank of England",
        "url": "https://www.bankofengland.co.uk/rss/news",
        "topic": "货币政策",
        "region": "英国",
        "description": "英格兰银行公开发布",
    },
    {
        "id": "treasury",
        "name": "U.S. Treasury",
        "url": "https://home.treasury.gov/news/press-releases.rss",
        "urls": ["https://home.treasury.gov/news/press-releases.rss", "https://home.treasury.gov/rss/press-releases.xml"],
        "topic": "财政政策",
        "region": "美国",
        "description": "美国财政部公开发布",
    },
]

FALLBACK_ITEMS = [
    {
        "id": "learn-fed-policy",
        "title": "如何阅读货币政策声明与利率决议",
        "summary": "从政策利率、经济评估和前瞻指引三个维度理解央行沟通。",
        "url": "https://www.federalreserve.gov/monetarypolicy.htm",
        "source": "Federal Reserve",
        "topic": "货币政策",
        "publishedAt": None,
        "isFallback": True,
    },
    {
        "id": "learn-imf-outlook",
        "title": "全球经济展望与政策风险",
        "summary": "查看 IMF 对增长、通胀、财政与外部风险的公开分析。",
        "url": "https://www.imf.org/en/Publications/WEO",
        "source": "IMF",
        "topic": "全球宏观",
        "publishedAt": None,
        "isFallback": True,
    },
    {
        "id": "learn-world-bank",
        "title": "全球发展与公共政策观察",
        "summary": "浏览世界银行关于经济发展、能源和公共政策的公开研究。",
        "url": "https://www.worldbank.org/en/research",
        "source": "World Bank",
        "topic": "政策与发展",
        "publishedAt": None,
        "isFallback": True,
    },
]


def _text(node: ET.Element | None, *names: str) -> str:
    if node is None:
        return ""
    for name in names:
        value = node.findtext(name)
        if value:
            return " ".join(value.split())
    return ""


def _parse_date(value: str) -> str | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
        except ValueError:
            return None


def _fetch_source(source: Dict[str, str], limit: int = 8) -> List[Dict[str, Any]]:
    last_error: Exception | None = None
    root = None
    for url in source.get("urls", [source["url"]]):
        try:
            request = Request(url, headers={"User-Agent": "StockResearchMVP/1.0 (public RSS reader)"})
            with urlopen(request, timeout=5) as response:  # nosec B310 - fixed HTTPS URLs above
                root = ET.fromstring(response.read())
            break
        except (HTTPError, URLError, TimeoutError, OSError, ET.ParseError) as exc:
            last_error = exc
    if root is None:
        raise RuntimeError(_source_error_reason(last_error)) from last_error

    entries = root.findall(".//item")
    if not entries:
        entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")

    items: List[Dict[str, Any]] = []
    for index, entry in enumerate(entries[:limit]):
        title = _plain_text(_text(entry, "title", "{http://www.w3.org/2005/Atom}title"))
        link = _text(entry, "link", "{http://www.w3.org/2005/Atom}link")
        if not link:
            link_node = entry.find("{http://www.w3.org/2005/Atom}link")
            link = link_node.attrib.get("href", "") if link_node is not None else ""
        summary = _plain_text(_text(entry, "description", "{http://www.w3.org/2005/Atom}summary", "{http://www.w3.org/2005/Atom}content"))
        published = _text(entry, "pubDate", "published", "updated", "{http://www.w3.org/2005/Atom}published", "{http://www.w3.org/2005/Atom}updated")
        publisher = _text(entry, "source") or source["name"]
        if title and link:
            language = detect_language(f"{title} {summary}")
            items.append({
                "id": f"{source['id']}-{index}-{link}",
                "title": title,
                "summary": summary[:280] if summary else source["description"],
                "url": link,
                "source": publisher,
                "topic": source["topic"],
                "region": source.get("region", "全球"),
                "language": language,
                "publishedAt": _parse_date(published),
                "isFallback": False,
            })
    return items


def _source_error_reason(error: Exception | None) -> str:
    if error is not None and error.__cause__ is not None:
        return _source_error_reason(error.__cause__)
    if isinstance(error, HTTPError):
        return f"HTTP {error.code}"
    if isinstance(error, (TimeoutError, URLError, OSError, ConnectionError)):
        return "网络超时或连接失败"
    if isinstance(error, ET.ParseError):
        return "返回内容不是有效 RSS/XML"
    return "请求或解析失败"


def _recommend(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Recent primary-source policy notices are favored.  Keep source diversity for a useful daily briefing.
    def sort_key(item: Dict[str, Any]) -> tuple:
        value = item.get("publishedAt") or "1970-01-01T00:00:00+00:00"
        return (not item.get("isFallback", False), value)

    chosen: List[Dict[str, Any]] = []
    sources = set()
    ordered = sorted(items, key=sort_key, reverse=True)
    for item in ordered:
        if item["source"] not in sources:
            chosen.append(item)
            sources.add(item["source"])
        if len(chosen) == 4:
            break
    for item in ordered:
        if item not in chosen:
            chosen.append(item)
        if len(chosen) == 4:
            break
    return chosen or FALLBACK_ITEMS[:3]


def get_daily_briefing() -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    with _cache_lock:
        if _cache["payload"] and _cache["expires_at"] > now:
            return _cache["payload"]

    items: List[Dict[str, Any]] = []
    warnings: List[str] = []
    # Public feeds have very different latency and blocking policies. Fetching
    # them concurrently keeps one slow publisher from blocking the whole brief.
    with ThreadPoolExecutor(max_workers=6) as executor:
        jobs = {executor.submit(_fetch_source, source): source for source in RSS_SOURCES}
        for job in as_completed(jobs):
            source = jobs[job]
            try:
                items.extend(job.result())
            except Exception as exc:
                warnings.append(f"{source['name']} 暂不可用（{_source_error_reason(exc)}），已保留其他公开来源。")

    if not items:
        items = FALLBACK_ITEMS.copy()
        warnings.append("实时资讯源暂不可用，当前展示官方学习资源卡片。")

    topics = ["全部", "货币政策", "全球宏观", "财政政策", "监管动态", "政策与发展", "美国市场", "欧洲市场", "日本市场", "新加坡市场", "香港市场"]
    payload = success_response(
        {"items": items, "recommended": _recommend(items), "topics": topics},
        {
            "source": "Official public feeds / regional Google News indexes",
            "last_updated": now_iso(),
            "timezone": "UTC",
            "adjusted": False,
            "delayed": True,
            "warnings": warnings,
        },
    )
    with _cache_lock:
        _cache.update({"expires_at": now + CACHE_TTL, "payload": payload})
    return payload
