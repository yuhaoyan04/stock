export function isFiniteNumber(value) {
  return value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value))
}

export function formatNumber(value, digits = 2, fallback = '-') {
  if (!isFiniteNumber(value)) return fallback
  return Number(value).toLocaleString('en-US', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

export function formatPrice(value, currency = '', digits = 2, fallback = '-') {
  if (!isFiniteNumber(value)) return fallback
  const prefix = currency && currency !== 'USD' ? `${currency} ` : ''
  return `${prefix}${formatNumber(value, digits, fallback)}`
}

export function formatPercent(value, options = {}) {
  const { input = 'ratio', digits = 2, signed = true, fallback = '-' } = options
  if (!isFiniteNumber(value)) return fallback
  const percent = input === 'percent' ? Number(value) : Number(value) * 100
  const sign = signed && percent > 0 ? '+' : ''
  return `${sign}${percent.toFixed(digits)}%`
}

export function formatChange(value, digits = 2, fallback = '-') {
  if (!isFiniteNumber(value)) return fallback
  const num = Number(value)
  const sign = num > 0 ? '+' : ''
  return `${sign}${num.toFixed(digits)}`
}

export function formatCompact(value, options = {}) {
  const { currency = '', digits = 2, fallback = '-' } = options
  if (!isFiniteNumber(value)) return fallback
  const num = Number(value)
  const abs = Math.abs(num)
  const prefix = currency ? `${currency}` : ''
  if (abs >= 1e12) return `${prefix}${(num / 1e12).toFixed(digits)}T`
  if (abs >= 1e9) return `${prefix}${(num / 1e9).toFixed(digits)}B`
  if (abs >= 1e6) return `${prefix}${(num / 1e6).toFixed(digits)}M`
  if (abs >= 1e3) return `${prefix}${(num / 1e3).toFixed(1)}K`
  return `${prefix}${num.toLocaleString('en-US', { maximumFractionDigits: digits })}`
}

export function valueClass(value) {
  if (!isFiniteNumber(value)) return ''
  return Number(value) >= 0 ? 'text-up' : 'text-down'
}

export function formatDateTime(value, fallback = '-') {
  if (!value) return fallback
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return fallback
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
