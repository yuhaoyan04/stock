"""
美股投资研究平台 — 后端 API 服务
FastAPI + yfinance
"""
from pathlib import Path

# ── 加载 .env 配置文件 ──────────────────────────────
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers import learning, market, news, portfolio, research, search, simulation, stock, translation

app = FastAPI(
    title="美股投资研究平台 API",
    description="基于 Yahoo Finance 的股票/ETF/指数/期货/外汇/加密货币数据服务",
    version="1.0.0",
)

# CORS — 允许 PWA 和前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(search.router)
app.include_router(stock.router)
app.include_router(market.router)
app.include_router(portfolio.router)
app.include_router(simulation.router)
app.include_router(research.router)
app.include_router(news.router)
app.include_router(learning.router)
app.include_router(translation.router)

# ── 生产环境：自动承载前端 PWA 静态文件 ────────────
FRONTEND_DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"
FRONTEND_ASSETS = FRONTEND_DIST / "assets"

if FRONTEND_DIST.exists() and FRONTEND_ASSETS.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_ASSETS)), name="assets")
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
