"""Research portfolio templates and comparison helpers."""
from copy import deepcopy
from typing import Any, Dict, List

from services.yfinance_service import compare_symbols
from utils.api_response import market_meta, success_response


DISCLOSURE_WARNING = "Public holdings and 13F-style data can be delayed and are not trading recommendations."

RESEARCH_PORTFOLIOS: List[Dict[str, Any]] = [
    {
        "id": "berkshire",
        "name": "Berkshire Hathaway Public Holdings",
        "manager": "Berkshire Hathaway",
        "source": "Public 13F-style holding snapshot, demo template",
        "disclosureDate": "2026-05-15",
        "asOfDate": "2026-03-31",
        "description": "A compact template of widely followed Berkshire public equity holdings for research workflow demos.",
        "benchmark": ["SPY", "QQQ"],
        "holdings": [
            {"symbol": "AAPL", "name": "Apple Inc.", "weight": 0.225, "sector": "Technology"},
            {"symbol": "AXP", "name": "American Express", "weight": 0.165, "sector": "Financial Services"},
            {"symbol": "BAC", "name": "Bank of America", "weight": 0.115, "sector": "Financial Services"},
            {"symbol": "KO", "name": "Coca-Cola", "weight": 0.085, "sector": "Consumer Defensive"},
            {"symbol": "CVX", "name": "Chevron", "weight": 0.075, "sector": "Energy"},
            {"symbol": "OXY", "name": "Occidental Petroleum", "weight": 0.065, "sector": "Energy"},
            {"symbol": "MCO", "name": "Moody's", "weight": 0.060, "sector": "Financial Services"},
            {"symbol": "KHC", "name": "Kraft Heinz", "weight": 0.050, "sector": "Consumer Defensive"},
            {"symbol": "CB", "name": "Chubb", "weight": 0.045, "sector": "Financial Services"},
            {"symbol": "DVA", "name": "DaVita", "weight": 0.035, "sector": "Healthcare"},
        ],
    },
    {
        "id": "ark_innovation",
        "name": "ARK Innovation Style Basket",
        "manager": "ARK-style innovation basket",
        "source": "Public ETF-themed demo template",
        "disclosureDate": "2026-07-01",
        "asOfDate": "2026-07-01",
        "description": "A simplified innovation-growth basket for comparing high-growth themes with broad benchmarks.",
        "benchmark": ["SPY", "QQQ"],
        "holdings": [
            {"symbol": "TSLA", "name": "Tesla", "weight": 0.160, "sector": "Consumer Cyclical"},
            {"symbol": "COIN", "name": "Coinbase", "weight": 0.130, "sector": "Financial Technology"},
            {"symbol": "ROKU", "name": "Roku", "weight": 0.105, "sector": "Communication Services"},
            {"symbol": "PLTR", "name": "Palantir", "weight": 0.095, "sector": "Technology"},
            {"symbol": "CRSP", "name": "CRISPR Therapeutics", "weight": 0.080, "sector": "Healthcare"},
            {"symbol": "SHOP", "name": "Shopify", "weight": 0.075, "sector": "Technology"},
            {"symbol": "SQ", "name": "Block", "weight": 0.070, "sector": "Financial Technology"},
            {"symbol": "PATH", "name": "UiPath", "weight": 0.060, "sector": "Technology"},
            {"symbol": "U", "name": "Unity Software", "weight": 0.055, "sector": "Technology"},
            {"symbol": "ZM", "name": "Zoom", "weight": 0.050, "sector": "Technology"},
        ],
    },
    {
        "id": "daily_journal",
        "name": "Charlie Munger — Daily Journal Concentrated Value",
        "manager": "Charlie Munger / Daily Journal Corp.",
        "source": "Representative value basket based on Daily Journal 13F filings",
        "disclosureDate": "2026-05-15",
        "asOfDate": "2026-03-31",
        "description": "The late Charlie Munger's approach through Daily Journal Corp. — extreme concentration, deep value, and a strong tilt toward financials. Munger believed in holding a few high-conviction bets for decades rather than diversifying broadly. This basket reflects that philosophy with heavy weights in quality banks and a dash of Chinese tech (BABA) that Munger championed despite drawdowns.",
        "benchmark": ["SPY", "QQQ"],
        "holdings": [
            {"symbol": "BAC", "name": "Bank of America", "weight": 0.22, "sector": "Financial Services"},
            {"symbol": "BABA", "name": "Alibaba Group ADR", "weight": 0.18, "sector": "Consumer Cyclical"},
            {"symbol": "USB", "name": "U.S. Bancorp", "weight": 0.14, "sector": "Financial Services"},
            {"symbol": "WFC", "name": "Wells Fargo & Co.", "weight": 0.10, "sector": "Financial Services"},
            {"symbol": "BRK-B", "name": "Berkshire Hathaway B", "weight": 0.09, "sector": "Financial Services"},
            {"symbol": "COST", "name": "Costco Wholesale", "weight": 0.08, "sector": "Consumer Defensive"},
            {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "weight": 0.07, "sector": "Financial Services"},
            {"symbol": "KHC", "name": "Kraft Heinz Co.", "weight": 0.06, "sector": "Consumer Defensive"},
            {"symbol": "MCO", "name": "Moody's Corp.", "weight": 0.04, "sector": "Financial Services"},
            {"symbol": "DVA", "name": "DaVita Inc.", "weight": 0.02, "sector": "Healthcare"},
        ],
    },
    {
        "id": "bridgewater_all_weather",
        "name": "Ray Dalio — Bridgewater All-Weather Style",
        "manager": "Ray Dalio / Bridgewater Associates",
        "source": "Representative ETF-based risk-parity template inspired by Bridgewater's All-Weather philosophy",
        "disclosureDate": "2026-05-15",
        "asOfDate": "2026-03-31",
        "description": "Dalio's All-Weather risk-parity framework balances assets that perform across inflation/growth regimes: equities (SPY), long-term Treasuries (TLT), intermediate Treasuries (IEF), gold (GLD), commodities (DBC), and emerging markets (EEM, VWO). This ETF-based basket approximates the strategy with liquid, low-cost instruments — favoring bonds and real assets over pure equity beta.",
        "benchmark": ["SPY", "AGG"],
        "holdings": [
            {"symbol": "SPY", "name": "SPDR S&P 500 ETF Trust", "weight": 0.20, "sector": "Technology"},
            {"symbol": "TLT", "name": "iShares 20+ Year Treasury Bond ETF", "weight": 0.18, "sector": "Financial Services"},
            {"symbol": "IEF", "name": "iShares 7-10 Year Treasury Bond ETF", "weight": 0.15, "sector": "Financial Services"},
            {"symbol": "GLD", "name": "SPDR Gold Shares ETF", "weight": 0.12, "sector": "Financial Services"},
            {"symbol": "DBC", "name": "Invesco DB Commodity Index Tracking", "weight": 0.10, "sector": "Energy"},
            {"symbol": "EEM", "name": "iShares MSCI Emerging Markets ETF", "weight": 0.09, "sector": "Financial Services"},
            {"symbol": "VWO", "name": "Vanguard FTSE Emerging Markets ETF", "weight": 0.07, "sector": "Financial Services"},
            {"symbol": "LQD", "name": "iShares iBoxx Investment Grade Corp Bond ETF", "weight": 0.05, "sector": "Financial Services"},
            {"symbol": "SHY", "name": "iShares 1-3 Year Treasury Bond ETF", "weight": 0.04, "sector": "Financial Services"},
        ],
    },
    {
        "id": "scion_asset",
        "name": "Michael Burry — Scion Asset Management Contrarian",
        "manager": "Michael Burry / Scion Asset Management",
        "source": "Representative contrarian basket based on Scion 13F filings",
        "disclosureDate": "2026-05-15",
        "asOfDate": "2026-03-31",
        "description": "Michael Burry, famous for betting against subprime mortgages in the 2008 crisis, runs a concentrated, deeply contrarian portfolio. He favors Chinese tech (BABA, JD), distressed assets, and out-of-favor value plays — often with asymmetric downside hedges. This basket reflects his recent 13F high-conviction bets on China internet, select financials, and special situations.",
        "benchmark": ["SPY", "QQQ"],
        "holdings": [
            {"symbol": "BABA", "name": "Alibaba Group ADR", "weight": 0.22, "sector": "Consumer Cyclical"},
            {"symbol": "JD", "name": "JD.com Inc. ADR", "weight": 0.18, "sector": "Consumer Cyclical"},
            {"symbol": "GOOGL", "name": "Alphabet Inc. Class A", "weight": 0.13, "sector": "Technology"},
            {"symbol": "BAC", "name": "Bank of America", "weight": 0.11, "sector": "Financial Services"},
            {"symbol": "CVX", "name": "Chevron Corp.", "weight": 0.10, "sector": "Energy"},
            {"symbol": "GEO", "name": "GEO Group Inc.", "weight": 0.09, "sector": "Industrials"},
            {"symbol": "CPRI", "name": "Capri Holdings Ltd.", "weight": 0.08, "sector": "Consumer Cyclical"},
            {"symbol": "GDX", "name": "VanEck Gold Miners ETF", "weight": 0.05, "sector": "Financial Services"},
            {"symbol": "RDFN", "name": "Redfin Corp.", "weight": 0.04, "sector": "Real Estate"},
        ],
    },
    {
        "id": "pershing_square",
        "name": "Bill Ackman — Pershing Square Concentrated Activist",
        "manager": "Bill Ackman / Pershing Square Capital Management",
        "source": "Representative activist basket based on Pershing Square 13F filings",
        "disclosureDate": "2026-05-15",
        "asOfDate": "2026-03-31",
        "description": "Bill Ackman runs one of the most concentrated activist hedge funds — typically 6-10 positions representing his highest-conviction bets. He takes large stakes, engages management, and holds for multi-year turnarounds. This basket captures his recent 13F top holdings with a mix of consumer, real estate, and tech exposure built around his 'simple and predictable' quality criterion.",
        "benchmark": ["SPY", "QQQ"],
        "holdings": [
            {"symbol": "CMG", "name": "Chipotle Mexican Grill", "weight": 0.22, "sector": "Consumer Cyclical"},
            {"symbol": "HLT", "name": "Hilton Worldwide Holdings", "weight": 0.18, "sector": "Consumer Cyclical"},
            {"symbol": "LOW", "name": "Lowe's Companies Inc.", "weight": 0.15, "sector": "Consumer Cyclical"},
            {"symbol": "GOOGL", "name": "Alphabet Inc. Class A", "weight": 0.14, "sector": "Technology"},
            {"symbol": "QSR", "name": "Restaurant Brands Intl.", "weight": 0.12, "sector": "Consumer Cyclical"},
            {"symbol": "CP", "name": "Canadian Pacific Kansas City", "weight": 0.10, "sector": "Industrials"},
            {"symbol": "PLD", "name": "Prologis Inc.", "weight": 0.05, "sector": "Real Estate"},
            {"symbol": "NKE", "name": "Nike Inc.", "weight": 0.04, "sector": "Consumer Cyclical"},
        ],
    },
    {
        "id": "duquesne_family",
        "name": "Stanley Druckenmiller — Duquesne Family Office",
        "manager": "Stanley Druckenmiller / Duquesne Family Office",
        "source": "Representative growth-bias basket based on Duquesne 13F filings",
        "disclosureDate": "2026-05-15",
        "asOfDate": "2026-03-31",
        "description": "Stanley Druckenmiller, who closed his legendary Duquesne Capital after 30 years of positive returns, now runs a family office with a concentrated, macro-informed equity book. He leans growth-heavy — dominant tech platforms (MSFT, NVDA, AMZN, GOOGL) plus high-moat healthcare (LLY). Druckenmiller is known for tactical agility, but his core holdings reflect long-term secular winners.",
        "benchmark": ["SPY", "QQQ"],
        "holdings": [
            {"symbol": "MSFT", "name": "Microsoft Corp.", "weight": 0.20, "sector": "Technology"},
            {"symbol": "NVDA", "name": "NVIDIA Corp.", "weight": 0.18, "sector": "Technology"},
            {"symbol": "AMZN", "name": "Amazon.com Inc.", "weight": 0.16, "sector": "Consumer Cyclical"},
            {"symbol": "GOOGL", "name": "Alphabet Inc. Class A", "weight": 0.14, "sector": "Technology"},
            {"symbol": "LLY", "name": "Eli Lilly & Co.", "weight": 0.10, "sector": "Healthcare"},
            {"symbol": "META", "name": "Meta Platforms Inc.", "weight": 0.09, "sector": "Technology"},
            {"symbol": "COIN", "name": "Coinbase Global Inc.", "weight": 0.05, "sector": "Financial Technology"},
            {"symbol": "CRM", "name": "Salesforce Inc.", "weight": 0.04, "sector": "Technology"},
            {"symbol": "PLTR", "name": "Palantir Technologies", "weight": 0.04, "sector": "Technology"},
        ],
    },
    {
        "id": "baupost_group",
        "name": "Seth Klarman — Baupost Group Deep Value",
        "manager": "Seth Klarman / Baupost Group",
        "source": "Representative deep-value basket based on Baupost 13F filings",
        "disclosureDate": "2026-05-15",
        "asOfDate": "2026-03-31",
        "description": "Seth Klarman, author of 'Margin of Safety,' runs Baupost Group with an almost obsessive focus on downside protection and deep value. The portfolio tilts toward special situations, discounted compounders, and beaten-down assets with catalysts. This basket reflects Baupost's recent preference for tech bargains (GOOGL), media spin-offs (LBRDA), and special-situation equities (VRT, FIS).",
        "benchmark": ["SPY", "QQQ"],
        "holdings": [
            {"symbol": "GOOGL", "name": "Alphabet Inc. Class A", "weight": 0.16, "sector": "Technology"},
            {"symbol": "LBRDA", "name": "Liberty Broadband Class A", "weight": 0.14, "sector": "Communication Services"},
            {"symbol": "FIS", "name": "Fidelity National Info. Svcs.", "weight": 0.12, "sector": "Technology"},
            {"symbol": "VRT", "name": "Vertiv Holdings Co.", "weight": 0.11, "sector": "Technology"},
            {"symbol": "BABA", "name": "Alibaba Group ADR", "weight": 0.10, "sector": "Consumer Cyclical"},
            {"symbol": "VIAC", "name": "Paramount Global Class B", "weight": 0.09, "sector": "Communication Services"},
            {"symbol": "VRSN", "name": "VeriSign Inc.", "weight": 0.08, "sector": "Technology"},
            {"symbol": "CHTR", "name": "Charter Communications", "weight": 0.07, "sector": "Communication Services"},
            {"symbol": "WBD", "name": "Warner Bros. Discovery", "weight": 0.07, "sector": "Communication Services"},
            {"symbol": "CNX", "name": "CNX Resources Corp.", "weight": 0.06, "sector": "Energy"},
        ],
    },
    {
        "id": "appaloosa_management",
        "name": "David Tepper — Appaloosa Management Macro/Tech",
        "manager": "David Tepper / Appaloosa Management",
        "source": "Representative macro-tech basket based on Appaloosa 13F filings",
        "disclosureDate": "2026-05-15",
        "asOfDate": "2026-03-31",
        "description": "David Tepper, one of the most successful distressed-debt and macro investors, runs a high-conviction portfolio with heavy tech exposure and tactical sector bets. Appaloosa's public equity book leans into mega-cap tech platforms (META, AMZN, MSFT, GOOGL) with select emerging-market growth (PDD) and financials. Tepper is known for bold, aggressive positioning — often going 'all-in' on his best ideas.",
        "benchmark": ["SPY", "QQQ"],
        "holdings": [
            {"symbol": "META", "name": "Meta Platforms Inc.", "weight": 0.20, "sector": "Technology"},
            {"symbol": "AMZN", "name": "Amazon.com Inc.", "weight": 0.17, "sector": "Consumer Cyclical"},
            {"symbol": "MSFT", "name": "Microsoft Corp.", "weight": 0.15, "sector": "Technology"},
            {"symbol": "GOOGL", "name": "Alphabet Inc. Class A", "weight": 0.13, "sector": "Technology"},
            {"symbol": "PDD", "name": "PDD Holdings Inc. ADR", "weight": 0.10, "sector": "Consumer Cyclical"},
            {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "weight": 0.08, "sector": "Financial Services"},
            {"symbol": "NVDA", "name": "NVIDIA Corp.", "weight": 0.07, "sector": "Technology"},
            {"symbol": "BAC", "name": "Bank of America", "weight": 0.05, "sector": "Financial Services"},
            {"symbol": "UBER", "name": "Uber Technologies Inc.", "weight": 0.03, "sector": "Technology"},
            {"symbol": "DIS", "name": "Walt Disney Co.", "weight": 0.02, "sector": "Communication Services"},
        ],
    },
    {
        "id": "vanguard_three_fund",
        "name": "三基金组合 Three-Fund Portfolio",
        "manager": "Vanguard index philosophy",
        "source": "Representative low-cost index portfolio template",
        "disclosureDate": "2026-07-01",
        "asOfDate": "2026-07-01",
        "description": "以美国股票、国际股票和债券三个资产桶构成的长期分散组合，适合学习资产类别与再平衡。",
        "benchmark": ["VTI", "BND"],
        "holdings": [
            {"symbol": "VTI", "name": "Vanguard Total Stock Market", "weight": 0.50, "sector": "US Equity"},
            {"symbol": "VXUS", "name": "Vanguard Total International Stock", "weight": 0.30, "sector": "International Equity"},
            {"symbol": "BND", "name": "Vanguard Total Bond Market", "weight": 0.20, "sector": "Fixed Income"},
        ],
    },
    {
        "id": "permanent_portfolio",
        "name": "Harry Browne Permanent Portfolio",
        "manager": "Harry Browne",
        "source": "Representative permanent-portfolio allocation template",
        "disclosureDate": "2026-07-01",
        "asOfDate": "2026-07-01",
        "description": "用股票、长期国债、现金与黄金各占一部分来理解跨场景分散；实际工具与税费需要单独研究。",
        "benchmark": ["SPY", "TLT"],
        "holdings": [
            {"symbol": "SPY", "name": "SPDR S&P 500 ETF", "weight": 0.25, "sector": "US Equity"},
            {"symbol": "TLT", "name": "iShares 20+ Year Treasury", "weight": 0.25, "sector": "Fixed Income"},
            {"symbol": "GLD", "name": "SPDR Gold Shares", "weight": 0.25, "sector": "Commodity"},
            {"symbol": "BIL", "name": "SPDR 1-3 Month T-Bill", "weight": 0.25, "sector": "Cash Equivalent"},
        ],
    },
    {
        "id": "global_60_40",
        "name": "全球 60/40 研究模板",
        "manager": "Asset allocation study template",
        "source": "Representative ETF research template",
        "disclosureDate": "2026-07-01",
        "asOfDate": "2026-07-01",
        "description": "将全球股票、美国股票与债券放进同一研究框架，观察地区分散对组合波动的影响。",
        "benchmark": ["SPY", "AGG"],
        "holdings": [
            {"symbol": "VTI", "name": "US Total Market", "weight": 0.35, "sector": "US Equity"},
            {"symbol": "VXUS", "name": "International Equity", "weight": 0.25, "sector": "International Equity"},
            {"symbol": "BND", "name": "US Bond Market", "weight": 0.30, "sector": "Fixed Income"},
            {"symbol": "GLD", "name": "Gold ETF", "weight": 0.10, "sector": "Commodity"},
        ],
    },
    {
        "id": "quality_dividend",
        "name": "质量与股息观察组合",
        "manager": "Educational factor basket",
        "source": "Representative factor-learning template",
        "disclosureDate": "2026-07-01",
        "asOfDate": "2026-07-01",
        "description": "用成熟企业和股息因子做观察样本，帮助学习行业分散、估值与现金流的关系。",
        "benchmark": ["SPY", "DIA"],
        "holdings": [
            {"symbol": "JNJ", "name": "Johnson & Johnson", "weight": 0.20, "sector": "Healthcare"},
            {"symbol": "PG", "name": "Procter & Gamble", "weight": 0.20, "sector": "Consumer Defensive"},
            {"symbol": "KO", "name": "Coca-Cola", "weight": 0.20, "sector": "Consumer Defensive"},
            {"symbol": "V", "name": "Visa", "weight": 0.20, "sector": "Financials"},
            {"symbol": "XOM", "name": "Exxon Mobil", "weight": 0.20, "sector": "Energy"},
        ],
    },
]


def _normalize_holdings(portfolio: Dict[str, Any]) -> Dict[str, Any]:
    result = deepcopy(portfolio)
    holdings = result.get("holdings", [])
    total = sum(float(item.get("weight", 0)) for item in holdings)
    if total > 0:
        for item in holdings:
            item["weight"] = round(float(item.get("weight", 0)) / total, 6)
    result["totalWeight"] = round(sum(item["weight"] for item in holdings), 6)
    result["warnings"] = [DISCLOSURE_WARNING]
    return result


def list_research_portfolios() -> Dict[str, Any]:
    portfolios = [
        {
            "id": item["id"],
            "name": item["name"],
            "manager": item["manager"],
            "source": item["source"],
            "disclosureDate": item["disclosureDate"],
            "asOfDate": item["asOfDate"],
            "holdingCount": len(item.get("holdings", [])),
            "warnings": [DISCLOSURE_WARNING],
        }
        for item in RESEARCH_PORTFOLIOS
    ]
    return success_response({"portfolios": portfolios}, market_meta(source="static research templates", warnings=[DISCLOSURE_WARNING]))


def get_research_portfolio(portfolio_id: str) -> Dict[str, Any]:
    for item in RESEARCH_PORTFOLIOS:
        if item["id"] == portfolio_id:
            portfolio = _normalize_holdings(item)
            return success_response(portfolio, market_meta(source=portfolio["source"], warnings=portfolio["warnings"]))
    raise ValueError("research portfolio not found")


def compare_research_portfolio(portfolio_id: str, period: str = "1y") -> Dict[str, Any]:
    portfolio = None
    for item in RESEARCH_PORTFOLIOS:
        if item["id"] == portfolio_id:
            portfolio = _normalize_holdings(item)
            break
    if portfolio is None:
        raise ValueError("research portfolio not found")

    symbols = [item["symbol"] for item in portfolio["holdings"][:5]] + portfolio.get("benchmark", ["SPY", "QQQ"])
    seen = []
    for symbol in symbols:
        if symbol not in seen:
            seen.append(symbol)
    comparison = compare_symbols(seen, period)
    return success_response(
        {
            "portfolioId": portfolio_id,
            "period": period,
            "symbols": seen,
            "comparison": comparison,
        },
        market_meta(source="yfinance", warnings=[DISCLOSURE_WARNING, "Comparison uses top holdings as a visual reference, not a replicated fund return."]),
    )
