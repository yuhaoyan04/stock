<template>
  <div class="stock-info-card">
    <div class="info-header">
      <div class="header-main">
        <h1 class="stock-name">{{ stock.name || stock.symbol }}</h1>
        <div class="stock-meta">
          <span class="stock-symbol">{{ stock.symbol }}</span>
          <el-tag v-if="stock.type" :type="getTagType(stock.type)" size="small">
            {{ getTypeLabel(stock.type) }}
          </el-tag>
          <span v-if="stock.exchange" class="exchange">{{ stock.exchange }}</span>
          <span v-if="stock.sector" class="sector">{{ stock.sector }}</span>
        </div>
      </div>
    </div>

    <div class="price-section">
      <div class="price-main">
        <span class="price-value">{{ formatPrice(stock.currentPrice) }}</span>
        <span class="currency">{{ stock.currency || 'USD' }}</span>
      </div>
      <div class="price-change" :class="changeClass">
        <span class="change-value">{{ formatChange(change) }}</span>
        <span class="change-pct">({{ formatPercent(changePercent) }})</span>
      </div>
    </div>

    <div class="info-grid">
      <div class="info-item">
        <span class="info-label">今开</span>
        <span class="info-value">{{ formatPrice(stock.open) }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">昨收</span>
        <span class="info-value">{{ formatPrice(stock.previousClose) }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">最高</span>
        <span class="info-value text-up">{{ formatPrice(stock.dayHigh) }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">最低</span>
        <span class="info-value text-down">{{ formatPrice(stock.dayLow) }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">52周高</span>
        <span class="info-value">{{ formatPrice(stock.fiftyTwoWeekHigh) }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">52周低</span>
        <span class="info-value">{{ formatPrice(stock.fiftyTwoWeekLow) }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">成交量</span>
        <span class="info-value">{{ formatVolume(stock.volume) }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">均量</span>
        <span class="info-value">{{ formatVolume(stock.avgVolume) }}</span>
      </div>
    </div>

    <!-- 估值指标 -->
    <div class="valuation-section" v-if="hasValuation">
      <h3 class="section-title">估值指标</h3>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">市值</span>
          <span class="info-value">{{ formatMarketCap(stock.marketCap) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">市盈率(PE)</span>
          <span class="info-value">{{ formatNumber(stock.peRatio) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">远期PE</span>
          <span class="info-value">{{ formatNumber(stock.forwardPE) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">PEG</span>
          <span class="info-value">{{ formatNumber(stock.pegRatio) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">市净率(PB)</span>
          <span class="info-value">{{ formatNumber(stock.priceToBook) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">市销率(PS)</span>
          <span class="info-value">{{ formatNumber(stock.priceToSales) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">EPS</span>
          <span class="info-value">{{ formatNumber(stock.eps) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">Beta</span>
          <span class="info-value">{{ formatNumber(stock.beta) }}</span>
        </div>
      </div>
    </div>

    <!-- 分红信息 -->
    <div class="dividend-section" v-if="hasDividend">
      <h3 class="section-title">分红信息</h3>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">股息率</span>
          <span class="info-value">{{ formatPercent(stock.dividendYield, true) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">每股分红</span>
          <span class="info-value">${{ formatNumber(stock.dividendRate) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">支付率</span>
          <span class="info-value">{{ formatPercent(stock.payoutRatio, true) }}</span>
        </div>
      </div>
    </div>

    <!-- 分析师评级 -->
    <div class="analyst-section" v-if="hasAnalyst">
      <h3 class="section-title">分析师评级</h3>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">目标均价</span>
          <span class="info-value">{{ formatPrice(stock.targetMeanPrice) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">目标高价</span>
          <span class="info-value">{{ formatPrice(stock.targetHighPrice) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">目标低价</span>
          <span class="info-value">{{ formatPrice(stock.targetLowPrice) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">评级</span>
          <span class="info-value">{{ ratingLabel }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">分析师数</span>
          <span class="info-value">{{ stock.numberOfAnalystOpinions }}</span>
        </div>
      </div>
    </div>

    <!-- 公司简介 -->
    <div class="description-section" v-if="stock.description">
      <h3 class="section-title">公司简介</h3>
      <p class="description-text">{{ stock.description }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  stock: { type: Object, default: () => ({}) },
})

const change = computed(() => {
  if (props.stock.currentPrice == null || props.stock.previousClose == null) return null
  return props.stock.currentPrice - props.stock.previousClose
})

const changePercent = computed(() => {
  if (change.value == null || props.stock.previousClose == null || Number(props.stock.previousClose) === 0) return null
  return (change.value / props.stock.previousClose) * 100
})

const changeClass = computed(() => {
  if (change.value == null) return ''
  return change.value >= 0 ? 'up' : 'down'
})

const hasValuation = computed(() => {
  const s = props.stock
  return s.marketCap || s.peRatio || s.priceToBook || s.eps || s.beta
})

const hasDividend = computed(() => {
  const s = props.stock
  return s.dividendRate || s.dividendYield
})

const hasAnalyst = computed(() => {
  const s = props.stock
  return s.targetMeanPrice || s.recommendationMean
})

const ratingLabel = computed(() => {
  const r = props.stock.recommendationMean
  if (r == null) return '—'
  if (r <= 1.5) return '强力买入'
  if (r <= 2.5) return '买入'
  if (r <= 3.5) return '持有'
  if (r <= 4.5) return '卖出'
  return '强力卖出'
})

function formatPrice(val) {
  if (val == null || val === undefined || !Number.isFinite(Number(val))) return '—'
  return Number(val).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function formatChange(val) {
  if (val == null || val === undefined || !Number.isFinite(Number(val))) return '—'
  const sign = val >= 0 ? '+' : ''
  return sign + Number(val).toFixed(2)
}

function formatPercent(val, multiply = false) {
  if (val == null || val === undefined || !Number.isFinite(Number(val))) return '—'
  const v = multiply ? Number(val) * 100 : Number(val)
  const sign = v >= 0 ? '+' : ''
  return sign + v.toFixed(2) + '%'
}

function formatNumber(val) {
  if (val == null || val === undefined || !Number.isFinite(Number(val))) return '—'
  return Number(val).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function formatVolume(val) {
  if (val == null || val === undefined || !Number.isFinite(Number(val))) return '—'
  if (val >= 1e9) return (val / 1e9).toFixed(2) + 'B'
  if (val >= 1e6) return (val / 1e6).toFixed(2) + 'M'
  if (val >= 1e3) return (val / 1e3).toFixed(1) + 'K'
  return val.toLocaleString()
}

function formatMarketCap(val) {
  if (val == null || val === undefined || !Number.isFinite(Number(val))) return '—'
  if (val >= 1e12) return '$' + (val / 1e12).toFixed(2) + 'T'
  if (val >= 1e9) return '$' + (val / 1e9).toFixed(2) + 'B'
  if (val >= 1e6) return '$' + (val / 1e6).toFixed(1) + 'M'
  return '$' + val.toLocaleString()
}

function getTypeLabel(type) {
  const map = {
    stock: '股票', etf: 'ETF', index: '指数',
    future: '期货', forex: '外汇', crypto: '加密',
  }
  return map[type] || type || ''
}

function getTagType(type) {
  const map = {
    stock: 'primary', etf: 'success', index: 'warning',
    future: 'danger', forex: 'info', crypto: '',
  }
  return map[type] || 'info'
}
</script>

<style lang="scss" scoped>
.stock-info-card {
  background-color: $bg-card;
  border: 1px solid $border-color;
  border-radius: $radius-lg;
  padding: 20px 24px;
}

.header-main {
  margin-bottom: 16px;
}

.stock-name {
  font-size: 22px;
  font-weight: 700;
  color: $text-primary;
  margin-bottom: 6px;
}

.stock-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.stock-symbol {
  font-size: 15px;
  font-weight: 600;
  color: $color-accent;
}

.exchange {
  font-size: 12px;
  color: $text-muted;
}

.sector {
  font-size: 12px;
  color: $text-secondary;
  background: $bg-hover;
  padding: 2px 8px;
  border-radius: $radius-sm;
}

.price-section {
  display: flex;
  align-items: baseline;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid $border-color;
}

.price-main {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.price-value {
  font-size: 32px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: $text-primary;
  letter-spacing: -0.5px;
}

.currency {
  font-size: 14px;
  color: $text-muted;
}

.price-change {
  font-size: 16px;
  font-weight: 600;

  &.up { color: $color-up; }
  &.down { color: $color-down; }

  .change-pct {
    font-size: 14px;
    opacity: 0.85;
    margin-left: 4px;
  }
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid $border-color;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px 20px;
  margin-bottom: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.info-label {
  font-size: 12px;
  color: $text-muted;
}

.info-value {
  font-size: 14px;
  font-weight: 500;
  color: $text-primary;
  font-variant-numeric: tabular-nums;
}

.valuation-section,
.dividend-section,
.analyst-section,
.description-section {
  margin-top: 12px;
}

.description-text {
  font-size: 13px;
  color: $text-secondary;
  line-height: 1.7;
}
</style>
