import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
})

api.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && typeof body === 'object' && Object.prototype.hasOwnProperty.call(body, 'success')) {
      response.meta = body.meta || {}
      response.apiError = body.error || null
      if (body.success === false) {
        const error = new Error(body.error?.message || 'API request failed')
        error.response = response
        throw error
      }
      response.data = body.data
    }
    return response
  },
  (error) => Promise.reject(error),
)

export function getApiErrorMessage(error, fallback = '请求失败，请稍后重试') {
  const detail = error?.response?.data?.detail
  if (detail?.error?.message) return detail.error.message
  if (detail?.message) return detail.message
  if (typeof detail === 'string') return detail
  if (error?.response?.apiError?.message) return error.response.apiError.message
  if (error?.message) return error.message
  return fallback
}

// ── 搜索 ──────────────────────────────────────────
export function searchSymbols(query, limit = 15) {
  return api.get('/search', { params: { q: query, limit } })
}

export function getCategories() {
  return api.get('/categories')
}

// ── 个股/资产 ──────────────────────────────────────
export function getStockInfo(symbol) {
  return api.get(`/stock/${encodeURIComponent(symbol)}/info`)
}

export function getStockHistory(symbol, period = '1mo', interval = '1d') {
  return api.get(`/stock/${encodeURIComponent(symbol)}/history`, { params: { period, interval } })
}

export function getFinancials(symbol, type = 'income', period = 'annual') {
  return api.get(`/stock/${encodeURIComponent(symbol)}/financials`, { params: { type, period } })
}

// ── 市场总览 ──────────────────────────────────────
export function getMarketOverview() {
  return api.get('/market/overview')
}

// ── 多资产对比 ────────────────────────────────────
export function compareSymbols(symbols, period = '1y') {
  return api.post('/market/compare', { symbols, period })
}

// ── 组合回测 ────────────────────────────────────
export function backtestPortfolio(payload) {
  return api.post('/portfolio/backtest', payload)
}


// ── 虚拟账户 / 模拟交易 ──────────────────────────
export function getSimulationAccount() {
  return api.get('/simulation/account')
}

export function getSimulationTrades(limit = 100) {
  return api.get('/simulation/trades', { params: { limit } })
}

export function getSimulationPendingOrders() {
  return api.get('/simulation/orders/pending')
}

export function cancelSimulationOrder(orderId) {
  return api.post(`/simulation/orders/${orderId}/cancel`)
}

export function getSimulationMarketStatus() {
  return api.get('/simulation/market-status')
}

export function submitSimulationOrder(payload) {
  return api.post('/simulation/orders', payload)
}

export function getSimulationTemplates() {
  return api.get('/simulation/templates')
}

export function buySimulationTemplate(payload) {
  return api.post('/simulation/template-orders', payload)
}

export function resetSimulationAccount() {
  return api.post('/simulation/reset')
}

// ── 研究组合 / 名人组合 ──────────────────────────
export function getResearchPortfolios() {
  return api.get('/research/portfolios')
}

export function getResearchPortfolio(id) {
  return api.get(`/research/portfolios/${encodeURIComponent(id)}`)
}

export function compareResearchPortfolio(id, period = '1y') {
  return api.get(`/research/portfolios/${encodeURIComponent(id)}/compare`, { params: { period } })
}

// ── 财经政策资讯 / 金融课堂 ───────────────────────
export function getDailyBriefing() {
  return api.get('/news/daily-briefing')
}

export function getLearningLessons() {
  return api.get('/learning/lessons')
}

export function translateTexts(texts, targetLanguage = 'zh-CN') {
  return api.post('/translation/texts', { texts, target_language: targetLanguage })
}
export default api
