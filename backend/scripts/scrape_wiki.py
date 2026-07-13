#!/usr/bin/env python3
"""
Wikipedia Financial Knowledge Scraper
======================================
Fetches 300+ financial term introductions from Wikipedia (freely licensed CC BY-SA),
formats them into lesson cards, and generates learning_service.py.

Usage:  python scripts/scrape_wiki.py

Wikipedia API respects: https://www.mediawiki.org/wiki/API:Main_page
Content license: CC BY-SA 4.0 — each card links back to the source article.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Topic list: (id_prefix, category, level, Wikipedia page title) ──────────
# 300+ financial terms organized by 17 categories
TOPICS: List[Tuple[str, str, str, str]] = [
    # ═══ 股票基础 (Stocks) ~28 ═══
    ("stock-basics", "股票", "入门", "Stock"),
    ("common-stock", "股票", "入门", "Common stock"),
    ("preferred-stock", "股票", "入门", "Preferred stock"),
    ("market-cap", "股票", "入门", "Market capitalization"),
    ("shares-outstanding", "股票", "入门", "Shares outstanding"),
    ("ipo-basics", "股票", "入门", "Initial public offering"),
    ("stock-exchange", "股票", "入门", "Stock exchange"),
    ("nyse", "股票", "入门", "New York Stock Exchange"),
    ("nasdaq", "股票", "入门", "Nasdaq"),
    ("stock-ticker", "股票", "入门", "Ticker symbol"),
    ("dividend-basics", "股票", "入门", "Dividend"),
    ("ex-dividend-date", "股票", "入门", "Ex-dividend date"),
    ("stock-split", "股票", "入门", "Stock split"),
    ("share-repurchase", "股票", "进阶", "Share repurchase"),
    ("secondary-offering", "股票", "进阶", "Secondary market offering"),
    ("adr-basics", "股票", "入门", "American depositary receipt"),
    ("blue-chip", "股票", "入门", "Blue chip (stock market)"),
    ("penny-stock", "股票", "入门", "Penny stock"),
    ("growth-stock", "股票", "入门", "Growth stock"),
    ("value-stock", "股票", "入门", "Value investing"),
    ("cyclical-stock", "股票", "进阶", "Cyclical stock"),
    ("defensive-stock", "股票", "进阶", "Defensive stock"),
    ("short-selling", "股票", "进阶", "Short (finance)"),
    ("margin-trading", "股票", "进阶", "Margin (finance)"),
    ("market-order", "股票", "入门", "Order (exchange)"),
    ("limit-order", "股票", "入门", "Limit order"),
    ("stop-order", "股票", "入门", "Stop order"),
    ("short-squeeze", "股票", "进阶", "Short squeeze"),

    # ═══ 财务报表 (Financial Statements) ~18 ═══
    ("income-statement", "财务报表", "入门", "Income statement"),
    ("revenue-recognition", "财务报表", "进阶", "Revenue recognition"),
    ("cogs", "财务报表", "入门", "Cost of goods sold"),
    ("gross-profit", "财务报表", "入门", "Gross income"),
    ("operating-income", "财务报表", "入门", "Earnings before interest and taxes"),
    ("net-income", "财务报表", "入门", "Net income"),
    ("eps", "财务报表", "入门", "Earnings per share"),
    ("balance-sheet", "财务报表", "入门", "Balance sheet"),
    ("current-assets", "财务报表", "入门", "Current asset"),
    ("fixed-assets", "财务报表", "入门", "Fixed asset"),
    ("goodwill", "财务报表", "进阶", "Goodwill (accounting)"),
    ("current-liabilities", "财务报表", "入门", "Current liability"),
    ("long-term-debt", "财务报表", "入门", "Long-term liabilities"),
    ("shareholders-equity", "财务报表", "入门", "Equity (finance)"),
    ("cash-flow-statement", "财务报表", "进阶", "Cash flow statement"),
    ("free-cash-flow", "财务报表", "进阶", "Free cash flow"),
    ("operating-cash-flow", "财务报表", "进阶", "Operating cash flow"),
    ("ebitda", "财务报表", "进阶", "Earnings before interest, taxes, depreciation and amortization"),

    # ═══ 财务比率 (Financial Ratios) ~22 ═══
    ("pe-ratio", "财务比率", "入门", "Price–earnings ratio"),
    ("pb-ratio", "财务比率", "入门", "P/B ratio"),
    ("ps-ratio", "财务比率", "入门", "Price–sales ratio"),
    ("peg-ratio", "财务比率", "进阶", "PEG ratio"),
    ("ev-ebitda", "财务比率", "进阶", "Enterprise value"),
    ("roe", "财务比率", "入门", "Return on equity"),
    ("roa", "财务比率", "入门", "Return on assets"),
    ("roic", "财务比率", "进阶", "Return on capital"),
    ("profit-margin", "财务比率", "入门", "Profit margin"),
    ("current-ratio", "财务比率", "入门", "Current ratio"),
    ("quick-ratio", "财务比率", "入门", "Quick ratio"),
    ("debt-ratio", "财务比率", "入门", "Debt ratio"),
    ("debt-to-equity", "财务比率", "入门", "Debt-to-equity ratio"),
    ("asset-turnover", "财务比率", "入门", "Asset turnover"),
    ("inventory-turnover", "财务比率", "进阶", "Inventory turnover"),
    ("dividend-yield", "财务比率", "入门", "Dividend yield"),
    ("dividend-payout-ratio", "财务比率", "进阶", "Dividend payout ratio"),
    ("dupont-analysis", "财务比率", "进阶", "DuPont analysis"),
    ("interest-coverage", "财务比率", "进阶", "Times interest earned"),
    ("beta-coefficient", "财务比率", "入门", "Beta (finance)"),
    ("market-cap-to-gdp", "财务比率", "进阶", "Buffett indicator"),
    ("sharpe-ratio", "财务比率", "进阶", "Sharpe ratio"),

    # ═══ 估值方法 (Valuation) ~16 ═══
    ("dcf-model", "估值方法", "进阶", "Discounted cash flow"),
    ("intrinsic-value", "估值方法", "进阶", "Intrinsic value (finance)"),
    ("wacc", "估值方法", "进阶", "Weighted average cost of capital"),
    ("capm", "估值方法", "进阶", "Capital asset pricing model"),
    ("equity-risk-premium", "估值方法", "进阶", "Equity risk premium"),
    ("dividend-discount-model", "估值方法", "进阶", "Dividend discount model"),
    ("comparable-company-analysis", "估值方法", "进阶", "Comparable company analysis"),
    ("precedent-transaction", "估值方法", "进阶", "Precedent transaction analysis"),
    ("margin-of-safety", "估值方法", "进阶", "Margin of safety (financial)"),
    ("terminal-value", "估值方法", "进阶", "Terminal value (finance)"),
    ("enterprise-value-to-revenue", "估值方法", "进阶", "Enterprise value"),
    ("book-value", "估值方法", "入门", "Book value"),
    ("liquidation-value", "估值方法", "进阶", "Liquidation value"),
    ("replacement-cost", "估值方法", "进阶", "Replacement value"),
    ("sum-of-parts", "估值方法", "进阶", "Sum-of-the-parts analysis"),
    ("residual-income-model", "估值方法", "进阶", "Residual income valuation"),

    # ═══ 技术分析 (Technical Analysis) ~32 ═══
    ("technical-analysis", "技术分析", "入门", "Technical analysis"),
    ("dow-theory", "技术分析", "入门", "Dow theory"),
    ("elliott-wave", "技术分析", "进阶", "Elliott wave principle"),
    ("moving-average", "技术分析", "入门", "Moving average"),
    ("golden-cross", "技术分析", "入门", "Golden cross"),
    ("death-cross", "技术分析", "入门", "Death cross"),
    ("bollinger-bands", "技术分析", "进阶", "Bollinger Bands"),
    ("macd", "技术分析", "进阶", "MACD"),
    ("rsi-indicator", "技术分析", "进阶", "Relative strength index"),
    ("stochastic-oscillator", "技术分析", "进阶", "Stochastic oscillator"),
    ("average-directional-index", "技术分析", "进阶", "Average directional movement index"),
    ("atr", "技术分析", "进阶", "Average true range"),
    ("obv", "技术分析", "进阶", "On-balance volume"),
    ("ichimoku-cloud", "技术分析", "进阶", "Ichimoku Kinkō Hyō"),
    ("fibonacci-retracement", "技术分析", "进阶", "Fibonacci retracement"),
    ("support-and-resistance", "技术分析", "入门", "Support and resistance"),
    ("head-and-shoulders", "技术分析", "进阶", "Head and shoulders (chart pattern)"),
    ("double-top", "技术分析", "进阶", "Double top and double bottom"),
    ("triangle-pattern", "技术分析", "进阶", "Triangle (chart pattern)"),
    ("flag-pattern", "技术分析", "进阶", "Flag and pennant patterns"),
    ("cup-and-handle", "技术分析", "进阶", "Cup and handle"),
    ("candlestick-pattern", "技术分析", "入门", "Candlestick pattern"),
    ("doji", "技术分析", "进阶", "Doji"),
    ("hammer-candlestick", "技术分析", "进阶", "Hammer (candlestick pattern)"),
    ("engulfing-pattern", "技术分析", "进阶", "Engulfing pattern"),
    ("volume-analysis", "技术分析", "入门", "Volume (finance)"),
    ("vwap", "技术分析", "进阶", "Volume-weighted average price"),
    ("point-and-figure", "技术分析", "进阶", "Point and figure chart"),
    ("renko-chart", "技术分析", "进阶", "Renko chart"),
    ("heikin-ashi", "技术分析", "进阶", "Heikin-Ashi"),
    ("pivot-point", "技术分析", "进阶", "Pivot point (technical analysis)"),
    ("parabolic-sar", "技术分析", "进阶", "Parabolic SAR"),

    # ═══ 衍生品 (Derivatives) ~30 ═══
    ("derivative-basics", "衍生品", "入门", "Derivative (finance)"),
    ("option-basics", "衍生品", "入门", "Option (finance)"),
    ("call-option", "衍生品", "入门", "Call option"),
    ("put-option", "衍生品", "入门", "Put option"),
    ("strike-price", "衍生品", "入门", "Strike price"),
    ("expiration-date", "衍生品", "入门", "Expiration (options)"),
    ("option-premium", "衍生品", "入门", "Option premium"),
    ("in-the-money", "衍生品", "入门", "Moneyness"),
    ("intrinsic-value-option", "衍生品", "进阶", "Intrinsic value (finance)"),
    ("time-value-option", "衍生品", "进阶", "Option time value"),
    ("delta-option", "衍生品", "进阶", "Greeks (finance)"),
    ("gamma-option", "衍生品", "进阶", "Greeks (finance)"),
    ("theta-option", "衍生品", "进阶", "Greeks (finance)"),
    ("vega-option", "衍生品", "进阶", "Greeks (finance)"),
    ("implied-volatility", "衍生品", "进阶", "Implied volatility"),
    ("volatility-smile", "衍生品", "进阶", "Volatility smile"),
    ("covered-call", "衍生品", "进阶", "Covered call"),
    ("protective-put", "衍生品", "进阶", "Protective put"),
    ("bull-spread", "衍生品", "进阶", "Bull spread"),
    ("bear-spread", "衍生品", "进阶", "Bear spread"),
    ("straddle-option", "衍生品", "进阶", "Straddle"),
    ("strangle-option", "衍生品", "进阶", "Strangle (options)"),
    ("iron-condor", "衍生品", "进阶", "Iron condor"),
    ("butterfly-spread", "衍生品", "进阶", "Butterfly (options)"),
    ("futures-contract", "衍生品", "入门", "Futures contract"),
    ("initial-margin", "衍生品", "入门", "Initial margin"),
    ("mark-to-market", "衍生品", "入门", "Mark-to-market accounting"),
    ("swap-derivative", "衍生品", "进阶", "Swap (finance)"),
    ("credit-default-swap", "衍生品", "进阶", "Credit default swap"),
    ("warrant-finance", "衍生品", "进阶", "Warrant (finance)"),

    # ═══ 固定收益 (Fixed Income) ~26 ═══
    ("bond-basics", "固定收益", "入门", "Bond (finance)"),
    ("treasury-bond", "固定收益", "入门", "United States Treasury security"),
    ("corporate-bond", "固定收益", "入门", "Corporate bond"),
    ("municipal-bond", "固定收益", "入门", "Municipal bond"),
    ("coupon-rate", "固定收益", "入门", "Coupon (finance)"),
    ("yield-to-maturity", "固定收益", "进阶", "Yield to maturity"),
    ("current-yield", "固定收益", "入门", "Current yield"),
    ("yield-curve", "固定收益", "进阶", "Yield curve"),
    ("inverted-yield-curve", "固定收益", "进阶", "Inverted yield curve"),
    ("duration-bond", "固定收益", "进阶", "Bond duration"),
    ("modified-duration", "固定收益", "进阶", "Modified duration"),
    ("convexity-bond", "固定收益", "进阶", "Bond convexity"),
    ("credit-rating", "固定收益", "入门", "Credit rating"),
    ("investment-grade", "固定收益", "入门", "Bond credit rating"),
    ("high-yield-bond", "固定收益", "进阶", "High-yield debt"),
    ("tips-bond", "固定收益", "入门", "Treasury Inflation-Protected Securities"),
    ("convertible-bond", "固定收益", "进阶", "Convertible bond"),
    ("callable-bond", "固定收益", "进阶", "Callable bond"),
    ("federal-funds-rate", "固定收益", "入门", "Federal funds rate"),
    ("repo-market", "固定收益", "进阶", "Repurchase agreement"),
    ("sofr", "固定收益", "进阶", "SOFR"),
    ("libor", "固定收益", "进阶", "Libor"),
    ("credit-spread", "固定收益", "进阶", "Credit spread (bond)"),
    ("bond-etf", "固定收益", "入门", "Bond exchange-traded fund"),
    ("immunization-strategy", "固定收益", "进阶", "Immunization (finance)"),
    ("riding-the-yield-curve", "固定收益", "进阶", "Riding the yield curve"),

    # ═══ 宏观经济学 (Macro Economics) ~32 ═══
    ("gdp", "宏观", "入门", "Gross domestic product"),
    ("inflation", "宏观", "入门", "Inflation"),
    ("cpi", "宏观", "入门", "Consumer price index"),
    ("ppi", "宏观", "入门", "Producer price index"),
    ("core-inflation", "宏观", "入门", "Core inflation"),
    ("unemployment-rate", "宏观", "入门", "Unemployment"),
    ("labor-force-participation", "宏观", "进阶", "Labor force participation rate"),
    ("pmi-manufacturing", "宏观", "进阶", "Purchasing Managers' Index"),
    ("ism-index", "宏观", "进阶", "Institute for Supply Management"),
    ("retail-sales", "宏观", "入门", "Retail sales"),
    ("consumer-confidence", "宏观", "进阶", "Consumer confidence index"),
    ("housing-starts", "宏观", "进阶", "Housing starts"),
    ("fiscal-policy", "宏观", "入门", "Fiscal policy"),
    ("monetary-policy", "宏观", "入门", "Monetary policy"),
    ("quantitative-easing", "宏观", "进阶", "Quantitative easing"),
    ("quantitative-tightening", "宏观", "进阶", "Quantitative tightening"),
    ("taylor-rule", "宏观", "进阶", "Taylor rule"),
    ("phillips-curve", "宏观", "进阶", "Phillips curve"),
    ("stagflation", "宏观", "入门", "Stagflation"),
    ("deflation", "宏观", "进阶", "Deflation"),
    ("hyperinflation", "宏观", "入门", "Hyperinflation"),
    ("trade-balance", "宏观", "入门", "Balance of trade"),
    ("current-account", "宏观", "进阶", "Current account (balance of payments)"),
    ("fiscal-deficit", "宏观", "进阶", "Government budget balance"),
    ("national-debt", "宏观", "入门", "National debt of the United States"),
    ("debt-to-gdp", "宏观", "进阶", "Debt-to-GDP ratio"),
    ("recession", "宏观", "入门", "Recession"),
    ("business-cycle", "宏观", "入门", "Business cycle"),
    ("leading-indicator", "宏观", "进阶", "Leading indicator"),
    ("sahm-rule", "宏观", "进阶", "Sahm rule"),
    ("misery-index", "宏观", "进阶", "Misery index (economics)"),
    ("real-interest-rate", "宏观", "进阶", "Real interest rate"),
]

# Extend with more topics to reach 300+
TOPICS.extend([
    # ═══ 行为金融 (Behavioral Finance) ~20 ═══
    ("behavioral-econ", "行为金融", "入门", "Behavioral economics"),
    ("loss-aversion", "行为金融", "入门", "Loss aversion"),
    ("overconfidence-bias", "行为金融", "进阶", "Overconfidence effect"),
    ("anchoring-bias", "行为金融", "入门", "Anchoring (cognitive bias)"),
    ("confirmation-bias", "行为金融", "入门", "Confirmation bias"),
    ("herd-behavior", "行为金融", "入门", "Herd behavior"),
    ("disposition-effect", "行为金融", "进阶", "Disposition effect"),
    ("endowment-effect", "行为金融", "进阶", "Endowment effect"),
    ("mental-accounting", "行为金融", "进阶", "Mental accounting"),
    ("framing-effect", "行为金融", "进阶", "Framing effect (psychology)"),
    ("sunk-cost-fallacy", "行为金融", "入门", "Sunk cost"),
    ("regret-aversion", "行为金融", "进阶", "Regret (decision theory)"),
    ("gamblers-fallacy", "行为金融", "入门", "Gambler's fallacy"),
    ("hindsight-bias", "行为金融", "进阶", "Hindsight bias"),
    ("availability-heuristic", "行为金融", "入门", "Availability heuristic"),
    ("representativeness-heuristic", "行为金融", "进阶", "Representativeness heuristic"),
    ("status-quo-bias", "行为金融", "进阶", "Status quo bias"),
    ("ambiguity-aversion", "行为金融", "进阶", "Ambiguity aversion"),
    ("prospect-theory", "行为金融", "进阶", "Prospect theory"),
    ("house-money-effect", "行为金融", "进阶", "House money effect"),

    # ═══ 组合管理 (Portfolio Management) ~20 ═══
    ("modern-portfolio-theory", "组合管理", "进阶", "Modern portfolio theory"),
    ("efficient-frontier", "组合管理", "进阶", "Efficient frontier"),
    ("capital-allocation-line", "组合管理", "进阶", "Capital allocation line"),
    ("capital-market-line", "组合管理", "进阶", "Capital market line"),
    ("sortino-ratio", "组合管理", "进阶", "Sortino ratio"),
    ("treynor-ratio", "组合管理", "进阶", "Treynor ratio"),
    ("information-ratio", "组合管理", "进阶", "Information ratio"),
    ("alpha-finance", "组合管理", "进阶", "Alpha (finance)"),
    ("r-squared", "组合管理", "进阶", "Coefficient of determination"),
    ("max-drawdown", "组合管理", "进阶", "Maximum drawdown"),
    ("calmar-ratio", "组合管理", "进阶", "Calmar ratio"),
    ("risk-parity", "组合管理", "进阶", "Risk parity"),
    ("black-litterman", "组合管理", "进阶", "Black–Litterman model"),
    ("core-satellite", "组合管理", "进阶", "Core-and-satellite portfolio"),
    ("rebalancing-portfolio", "组合管理", "入门", "Rebalancing investments"),
    ("asset-allocation", "组合管理", "入门", "Asset allocation"),
    ("diversification", "组合管理", "入门", "Diversification (finance)"),
    ("barbell-strategy", "组合管理", "进阶", "Barbell strategy"),
    ("endowment-model", "组合管理", "进阶", "Endowment model"),
    ("risk-budgeting", "组合管理", "进阶", "Risk budgeting"),

    # ═══ 因子投资 (Factor Investing) ~14 ═══
    ("factor-investing", "因子投资", "进阶", "Factor investing"),
    ("value-factor", "因子投资", "进阶", "Value investing"),
    ("momentum-factor", "因子投资", "进阶", "Momentum investing"),
    ("size-factor", "因子投资", "进阶", "Size premium"),
    ("quality-factor", "因子投资", "进阶", "Quality investing"),
    ("low-volatility-factor", "因子投资", "进阶", "Low-volatility investing"),
    ("smart-beta", "因子投资", "进阶", "Smart beta"),
    ("fama-french", "因子投资", "进阶", "Fama–French three-factor model"),
    ("carhart-four-factor", "因子投资", "进阶", "Carhart four-factor model"),
    ("factor-crowding", "因子投资", "进阶", "Factor investing"),
    ("factor-timing", "因子投资", "进阶", "Market timing"),
    ("fundamental-indexing", "因子投资", "进阶", "Fundamental indexing"),
    ("equal-weight-index", "因子投资", "入门", "Equal weight"),
    ("cap-weighted-index", "因子投资", "入门", "Capitalization-weighted index"),

    # ═══ 外汇 (Forex) ~15 ═══
    ("foreign-exchange", "外汇", "入门", "Foreign exchange market"),
    ("currency-pair", "外汇", "入门", "Currency pair"),
    ("exchange-rate", "外汇", "入门", "Exchange rate"),
    ("fixed-exchange-rate", "外汇", "进阶", "Fixed exchange rate system"),
    ("floating-exchange-rate", "外汇", "进阶", "Floating exchange rate"),
    ("purchasing-power-parity", "外汇", "进阶", "Purchasing power parity"),
    ("interest-rate-parity", "外汇", "进阶", "Interest rate parity"),
    ("carry-trade", "外汇", "进阶", "Carry (investment)"),
    ("forex-reserves", "外汇", "入门", "Foreign exchange reserves"),
    ("currency-intervention", "外汇", "进阶", "Currency intervention"),
    ("devaluation", "外汇", "进阶", "Devaluation"),
    ("currency-peg", "外汇", "进阶", "Fixed exchange rate system"),
    ("forex-swap", "外汇", "进阶", "Foreign exchange swap"),
    ("britton-woods", "外汇", "入门", "Bretton Woods system"),
    ("special-drawing-rights", "外汇", "进阶", "Special drawing rights"),

    # ═══ 大宗商品 (Commodities) ~16 ═══
    ("commodity-market", "商品", "入门", "Commodity market"),
    ("spot-price", "商品", "入门", "Spot contract"),
    ("futures-price", "商品", "入门", "Futures exchange"),
    ("contango", "商品", "进阶", "Contango"),
    ("backwardation", "商品", "进阶", "Backwardation"),
    ("crude-oil-types", "商品", "入门", "Benchmark (crude oil)"),
    ("opec", "商品", "入门", "OPEC"),
    ("gold-reserve", "商品", "入门", "Gold reserve"),
    ("london-metal-exchange", "商品", "进阶", "London Metal Exchange"),
    ("copper-doctor", "商品", "进阶", "Doctor Copper"),
    ("agricultural-commodities", "商品", "入门", "Commodity market"),
    ("commodity-etf", "商品", "入门", "Commodity Exchange-Traded Fund"),
    ("roll-yield", "商品", "进阶", "Roll yield"),
    ("carbon-credit", "商品", "进阶", "Carbon emission trading"),
    ("strategic-petroleum-reserve", "商品", "进阶", "Strategic Petroleum Reserve (United States)"),
    ("commodity-super-cycle", "商品", "进阶", "Commodity price shocks"),

    # ═══ 加密资产 (Crypto) ~14 ═══
    ("blockchain", "加密资产", "入门", "Blockchain"),
    ("bitcoin", "加密资产", "入门", "Bitcoin"),
    ("ethereum", "加密资产", "入门", "Ethereum"),
    ("proof-of-work", "加密资产", "入门", "Proof of work"),
    ("proof-of-stake", "加密资产", "入门", "Proof of stake"),
    ("defi", "加密资产", "进阶", "Decentralized finance"),
    ("stablecoin", "加密资产", "入门", "Stablecoin"),
    ("nft", "加密资产", "入门", "Non-fungible token"),
    ("crypto-exchange", "加密资产", "进阶", "Cryptocurrency exchange"),
    ("crypto-wallet", "加密资产", "入门", "Cryptocurrency wallet"),
    ("smart-contract", "加密资产", "进阶", "Smart contract"),
    ("bitcoin-etf", "加密资产", "入门", "Bitcoin spot exchange-traded fund"),
    ("bitcoin-halving", "加密资产", "进阶", "Bitcoin halving"),
    ("ethereum-gas", "加密资产", "进阶", "Ethereum"),

    # ═══ 基金/ETF ~15 ═══
    ("etf-structure", "基金", "入门", "Exchange-traded fund"),
    ("authorized-participant", "基金", "进阶", "Authorized participant"),
    ("tracking-error", "基金", "进阶", "Tracking error"),
    ("expense-ratio", "基金", "入门", "Expense ratio"),
    ("etf-premium-discount", "基金", "进阶", "Exchange-traded fund"),
    ("mutual-fund", "基金", "入门", "Mutual fund"),
    ("index-fund", "基金", "入门", "Index fund"),
    ("hedge-fund", "基金", "进阶", "Hedge fund"),
    ("private-equity", "基金", "进阶", "Private equity"),
    ("venture-capital", "基金", "进阶", "Venture capital"),
    ("closed-end-fund", "基金", "进阶", "Closed-end fund"),
    ("leveraged-etf", "基金", "进阶", "Leveraged ETF"),
    ("inverse-etf", "基金", "进阶", "Inverse exchange-traded fund"),
    ("money-market-fund", "基金", "入门", "Money market fund"),
    ("target-date-fund", "基金", "入门", "Target date fund"),

    # ═══ 房地产 (Real Estate) ~12 ═══
    ("reit", "房地产", "入门", "Real estate investment trust"),
    ("equity-reit", "房地产", "进阶", "Equity REIT"),
    ("mortgage-reit", "房地产", "进阶", "Mortgage REIT"),
    ("ffo", "房地产", "进阶", "Funds from operations"),
    ("capitalization-rate", "房地产", "进阶", "Capitalization rate"),
    ("net-operating-income", "房地产", "进阶", "Net operating income"),
    ("commercial-real-estate", "房地产", "入门", "Commercial property"),
    ("residential-real-estate", "房地产", "入门", "Real estate economics"),
    ("mortgage-backed-security", "房地产", "进阶", "Mortgage-backed security"),
    ("subprime-mortgage", "房地产", "进阶", "Subprime lending"),
    ("home-equity", "房地产", "入门", "Home equity"),
    ("real-estate-bubble", "房地产", "进阶", "Real-estate bubble"),

    # ═══ 个人理财 (Personal Finance) ~16 ═══
    ("compound-interest", "个人理财", "入门", "Compound interest"),
    ("ira-account", "个人理财", "入门", "Individual retirement account"),
    ("roth-ira", "个人理财", "入门", "Roth IRA"),
    ("traditional-ira", "个人理财", "入门", "Traditional IRA"),
    ("floor-401k", "个人理财", "入门", "401(k)"),
    ("capital-gains-tax", "个人理财", "入门", "Capital gains tax"),
    ("tax-loss-harvesting", "个人理财", "进阶", "Tax-loss harvesting"),
    ("wash-sale-rule", "个人理财", "进阶", "Wash sale"),
    ("withdrawal-rule-four-percent", "个人理财", "进阶", "Trinity study"),
    ("emergency-fund", "个人理财", "入门", "Rainy day fund"),
    ("dollar-cost-averaging", "个人理财", "入门", "Dollar cost averaging"),
    ("credit-score", "个人理财", "入门", "Credit score"),
    ("inflation-hedge", "个人理财", "入门", "Inflation hedge"),
    ("rule-of-72", "个人理财", "入门", "Rule of 72"),
    ("fiduciary-duty", "个人理财", "进阶", "Fiduciary"),
    ("estate-planning", "个人理财", "进阶", "Estate planning"),

    # ═══ 风险管理 (Risk Management) ~14 ═══
    ("value-at-risk", "风险管理", "进阶", "Value at risk"),
    ("expected-shortfall", "风险管理", "进阶", "Expected shortfall"),
    ("stress-testing", "风险管理", "进阶", "Stress test (financial)"),
    ("black-swan-theory", "风险管理", "进阶", "Black swan theory"),
    ("systemic-risk", "风险管理", "进阶", "Systemic risk"),
    ("liquidity-risk", "风险管理", "进阶", "Liquidity risk"),
    ("counterparty-risk", "风险管理", "进阶", "Counterparty risk"),
    ("operational-risk", "风险管理", "进阶", "Operational risk"),
    ("model-risk", "风险管理", "进阶", "Model risk"),
    ("fat-tail-risk", "风险管理", "进阶", "Fat-tailed distribution"),
    ("kurtosis-risk", "风险管理", "进阶", "Kurtosis"),
    ("hedging", "风险管理", "进阶", "Hedge (finance)"),
    ("stop-loss-order", "风险管理", "入门", "Stop loss order"),
    ("basel-iii", "风险管理", "进阶", "Basel III"),

    # ═══ 公司金融 (Corporate Finance) ~12 ═══
    ("mergers-acquisitions", "公司金融", "进阶", "Mergers and acquisitions"),
    ("leveraged-buyout", "公司金融", "进阶", "Leveraged buyout"),
    ("capital-structure", "公司金融", "进阶", "Capital structure"),
    ("cost-of-capital", "公司金融", "进阶", "Cost of capital"),
    ("corporate-governance", "公司金融", "进阶", "Corporate governance"),
    ("proxy-voting", "公司金融", "进阶", "Proxy voting"),
    ("activist-investor", "公司金融", "进阶", "Activist shareholder"),
    ("poison-pill", "公司金融", "进阶", "Shareholder rights plan"),
    ("tender-offer", "公司金融", "进阶", "Tender offer"),
    ("spin-off", "公司金融", "进阶", "Corporate spin-off"),
    ("dividend-policy", "公司金融", "进阶", "Dividend policy"),
    ("economic-value-added", "公司金融", "进阶", "Economic value added"),
])


# ── Wikipedia API ────────────────────────────────────────────────────────────
WIKI_API = "https://en.wikipedia.org/w/api.php"

# Ticker mapping: suggest related market symbols for each category
CATEGORY_TICKERS: Dict[str, List[str]] = {
    "股票": ["SPY", "AAPL", "MSFT"],
    "财务报表": ["AAPL", "MSFT", "AMZN"],
    "财务比率": ["SPY", "QQQ", "AAPL"],
    "估值方法": ["SPY", "AAPL", "BRK-B"],
    "技术分析": ["SPY", "AAPL", "QQQ"],
    "衍生品": ["SPY", "^VIX", "QQQ"],
    "固定收益": ["TLT", "IEF", "LQD"],
    "宏观": ["^TNX", "SPY", "CL=F"],
    "行为金融": ["SPY", "^VIX", "BTC-USD"],
    "组合管理": ["SPY", "TLT", "GLD"],
    "因子投资": ["VTV", "MTUM", "QUAL"],
    "外汇": ["DX-Y.NYB", "EURUSD=X", "JPY=X"],
    "商品": ["CL=F", "GC=F", "DBC"],
    "加密资产": ["BTC-USD", "ETH-USD", "SOL-USD"],
    "基金": ["SPY", "QQQ", "IWM"],
    "房地产": ["VNQ", "PLD", "O"],
    "个人理财": ["SPY", "SCHD", "QQQ"],
    "风险管理": ["SPY", "^VIX", "TLT"],
    "公司金融": ["SPY", "BRK-B", "JPM"],
}


def fetch_wiki_extract(title: str, max_retries: int = 3) -> Optional[Dict[str, str]]:
    """Fetch the introduction extract of a Wikipedia page, with retry logic."""
    params = {
        "action": "query",
        "prop": "extracts",
        "exintro": "1",
        "explaintext": "1",
        "titles": title,
        "format": "json",
        "redirects": "1",
    }
    url = f"{WIKI_API}?{urllib.parse.urlencode(params)}"
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "StockResearchEdu/1.0 (public education scraper; contact me@example.com)"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 429:
                    wait = (attempt + 1) * 5
                    print(f"  [RATE-LIMIT] Waiting {wait}s before retry...", file=sys.stderr)
                    time.sleep(wait)
                    continue
                data = json.loads(resp.read())
            pages = data.get("query", {}).get("pages", {})
            for _page_id, page in pages.items():
                if "missing" in page:
                    return None
                return {
                    "title": page.get("title", title),
                    "extract": page.get("extract", ""),
                }
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = (attempt + 1) * 5
                print(f"  [RATE-LIMIT] HTTP 429, waiting {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            print(f"  [WARN] HTTP {e.code} for '{title}'", file=sys.stderr)
            return None
        except Exception as exc:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            print(f"  [WARN] Failed to fetch '{title}': {exc}", file=sys.stderr)
            return None
    return None


def clean_extract(text: str, max_len: int = 320) -> str:
    """Clean Wikipedia extract into a compact summary."""
    # Remove parenthetical references like (NYSE: AAPL)
    import re
    text = re.sub(r'\s*\([^)]*(?:NYSE|NASDAQ|LSE|FWB|TYO)[^)]*\)', '', text)
    text = re.sub(r'\s*\[[^\]]*\]', '', text)  # Remove citation brackets
    text = ' '.join(text.split())  # Normalize whitespace
    if len(text) > max_len:
        # Cut at last complete sentence within limit
        cut = text.rfind('. ', 0, max_len)
        if cut > max_len // 2:
            text = text[:cut + 1]
        else:
            text = text[:max_len].rsplit(' ', 1)[0] + '…'
    return text


def extract_takeaways(text: str, count: int = 3) -> List[str]:
    """Extract key takeaways by splitting into sentences and picking substantive ones."""
    import re
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    # Filter: keep sentences with meaningful length and no introductory fluff
    good = []
    for s in sentences:
        s = s.strip()
        if 25 < len(s) < 200 and not s.lower().startswith(('this article', 'for more', 'see also', 'note that')):
            good.append(s)
    # Pick first 'count' sentences from different parts of the text
    if len(good) <= count:
        return good[:count]
    # Pick first, one from middle, and last
    n = len(good)
    picks = [good[0]]
    if count >= 2:
        picks.append(good[n // 2])
    if count >= 3:
        picks.append(good[-1])
    return [p[:150] + ('…' if len(p) > 150 else '') for p in picks]


def title_to_name(page_title: str) -> str:
    """Map Wikipedia page title to a Chinese-friendly display name."""
    # Strip disambiguation like " (finance)" or " (economics)"
    import re
    return re.sub(r'\s*\([^)]*\)$', '', page_title)


def build_card(wiki_data: Dict[str, str], topic: Tuple[str, str, str, str]) -> Dict[str, Any]:
    """Build a lesson card from topic definition + Wikipedia extract."""
    card_id, category, level, wiki_title = topic
    extract = wiki_data["extract"]
    page_title = wiki_data.get("title", wiki_title)

    summary = clean_extract(extract)
    takeaways = extract_takeaways(extract)

    # Ensure we have at least 2 takeaways
    if len(takeaways) < 2:
        sentences = [s.strip() for s in extract.split('. ') if 20 < len(s.strip()) < 200]
        while len(takeaways) < 3 and len(sentences) > len(takeaways):
            s = sentences[len(takeaways)]
            if s not in takeaways:
                takeaways.append(s[:150] + ('…' if len(s) > 150 else ''))

    if len(takeaways) < 2:
        takeaways = [
            f"了解{page_title}的基本定义和应用场景",
            f"理解{page_title}在金融市场中的作用和影响",
            f"结合市场数据观察{page_title}的实际表现",
        ]

    tickers = CATEGORY_TICKERS.get(category, ["SPY", "QQQ"])
    source_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(wiki_title.replace(' ', '_'))}"

    return {
        "id": card_id,
        "level": level,
        "category": category,
        "title": f"{page_title}——{summary[:60]}…" if len(summary) > 60 else f"{page_title}——{summary}",
        "summary": summary,
        "takeaways": takeaways[:3],
        "marketLinks": tickers,
        "sourceName": "Wikipedia / CC BY-SA 4.0",
        "sourceUrl": source_url,
    }


def generate(num_lessons: int = 0) -> str:
    """
    Generate learning_service.py content by scraping Wikipedia for each topic.
    Set num_lessons > 0 to limit how many to scrape (0 = all).
    """
    topics = TOPICS[:num_lessons] if num_lessons > 0 else TOPICS
    total = len(topics)
    lessons = []
    failures = []

    print(f"Fetching {total} Wikipedia extracts...")
    for i, topic in enumerate(topics):
        card_id, category, level, wiki_title = topic
        pct = (i + 1) * 100 // total
        print(f"  [{pct:3d}%] {wiki_title}")

        wiki_data = fetch_wiki_extract(wiki_title)
        if wiki_data is None or not wiki_data.get("extract"):
            failures.append(wiki_title)
            continue

        try:
            card = build_card(wiki_data, topic)
            lessons.append(card)
        except Exception as exc:
            print(f"  [ERROR] Failed to build card for '{wiki_title}': {exc}", file=sys.stderr)
            failures.append(wiki_title)

        # Be kind to Wikipedia: 0.5s delay between each request, longer every 15
        delay = 1.0 if (i + 1) % 15 == 0 else 0.25
        time.sleep(delay)

    print(f"\nDone. {len(lessons)} cards generated, {len(failures)} failures.")
    if failures:
        print(f"Failed topics: {failures}", file=sys.stderr)

    # Generate the Python module using json.dumps for safe string escaping
    lesson_lines = []
    for card in lessons:
        line = json.dumps(card, ensure_ascii=False)
        lesson_lines.append(f"    {line},")

    lessons_text = "\n".join(lesson_lines)

    module = f'''"""Curated finance learning cards — generated from Wikipedia (CC BY-SA 4.0).
Content is educational, not investment advice. Source attribution inline per card.
"""
from typing import Any, Dict, List

from utils.api_response import now_iso, success_response


LESSONS: List[Dict[str, Any]] = [
{lessons_text}
]


def list_lessons() -> Dict[str, Any]:
    categories = ["全部"] + list(dict.fromkeys(item["category"] for item in LESSONS))
    return success_response(
        {{"lessons": LESSONS, "categories": categories}},
        {{
            "source": "Wikipedia CC BY-SA 4.0 + curated public education resources",
            "last_updated": now_iso(),
            "timezone": "UTC",
            "adjusted": False,
            "delayed": False,
            "warnings": ["课程内容用于金融教育与研究，不构成投资建议。来源：Wikipedia (CC BY-SA 4.0) 及公共教育资源。"],
        }},
    )
'''

    return module


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate learning_service.py from Wikipedia")
    parser.add_argument("-n", "--num", type=int, default=60, help="Number of topics to scrape (0=all, default 60 for testing)")
    parser.add_argument("-o", "--output", type=str, default=None, help="Output file path")
    parser.add_argument("--all", action="store_true", help="Scrape ALL topics (~300+)")
    parser.add_argument("--cleanup", action="store_true", help="Clean up card titles to be shorter")
    args = parser.parse_args()

    if args.all:
        args.num = 0

    print(f"Wikipedia Financial Knowledge Scraper")
    print(f"======================================")
    print(f"Topics to scrape: {'ALL' if args.num == 0 else args.num}")
    print()

    code = generate(num_lessons=args.num)

    # Cleanup titles if requested
    if args.cleanup and '——' in code:
        import re
        code = re.sub(r'"title":"([^"]+)——[^"]*"', r'"title":"\1"', code)

    out_path = Path(args.output) if args.output else Path(__file__).resolve().parents[1] / "services" / "learning_service.py"
    out_path.write_text(code, encoding="utf-8")
    print(f"\nWritten to: {out_path}")
    card_count = code.count('"id":')
    print(f"Total cards: {card_count}")
