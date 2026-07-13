<template>
  <div class="portfolio-page">
    <div class="page-header">
      <div>
        <h1>组合实验室</h1>
        <p>校验资产池、权重和参数后运行历史回测，结果仅用于研究和教学。</p>
      </div>
      <el-tag type="warning" size="small">非投资建议</el-tag>
    </div>
    <ModuleGuide title="组合实验室" description="用于在统一假设下比较多个资产的历史组合表现。" :steps="['搜索并添加至少一个有效 ticker。', '选择回测区间、策略、基准、再平衡和成本参数。', '运行后重点阅读回撤、数据区间、权重与警告信息。']" note="回测不等于预测，交易成本和历史可得数据会显著影响结果。" class="mb-4" />

    <div class="control-panel">
      <div class="search-row">
        <el-select
          v-model="selectedAsset"
          filterable
          remote
          reserve-keyword
          placeholder="搜索并添加股票、ETF、指数..."
          :remote-method="searchAssets"
          :loading="searchLoading"
          clearable
          value-key="symbol"
          class="asset-search"
          @change="addAsset"
        >
          <el-option v-for="item in searchResults" :key="item.symbol" :label="item.symbol" :value="item">
            <div class="search-option">
              <span class="opt-symbol">{{ item.symbol }}</span>
              <span class="opt-name">{{ item.name }}</span>
              <el-tag size="small">{{ getTypeLabel(item.type) }}</el-tag>
            </div>
          </el-option>
        </el-select>

        <el-select v-model="period" class="small-select">
          <el-option label="1个月" value="1mo" />
          <el-option label="3个月" value="3mo" />
          <el-option label="6个月" value="6mo" />
          <el-option label="1年" value="1y" />
          <el-option label="2年" value="2y" />
          <el-option label="5年" value="5y" />
          <el-option label="10年" value="10y" />
        </el-select>

        <el-select v-model="mode" class="mode-select">
          <el-option label="等权" value="equal" />
          <el-option label="自定义权重" value="custom" />
          <el-option label="风险平价" value="risk_parity" />
          <el-option label="最小方差" value="min_variance" />
          <el-option label="最大夏普" value="max_sharpe" />
        </el-select>

        <el-input v-model="benchmark" class="benchmark-input" placeholder="基准" />

        <el-button type="primary" :loading="running" :disabled="assets.length === 0" @click="runBacktest">
          运行回测
        </el-button>
      </div>

      <div class="allocation-toolbar">
        <span class="toolbar-label">权重工具</span>
        <el-button size="small" :type="mode === 'custom' ? 'primary' : 'default'" @click="enableCustomWeights">
          手动调节比例
        </el-button>
        <el-select v-model="optimizationMode" size="small" class="optimization-select">
          <el-option label="最小方差" value="min_variance" />
          <el-option label="最大夏普" value="max_sharpe" />
          <el-option label="风险平价" value="risk_parity" />
        </el-select>
        <el-button size="small" type="success" :loading="running" :disabled="assets.length === 0" @click="calculateOptimal">
          计算最优配置
        </el-button>
        <span class="toolbar-hint">优化结果基于历史数据，完成后可应用为可编辑比例。</span>
      </div>

      <div class="asset-tags" v-if="assets.length">
        <el-tag v-for="asset in assets" :key="asset.symbol" closable size="large" class="asset-tag" @close="removeAsset(asset.symbol)">
          {{ asset.symbol }}
        </el-tag>
      </div>
    </div>

    <StateBlock v-if="errorMessage" type="error" title="回测失败" :description="errorMessage" class="mb-4" compact />
    <DataQualityBar v-if="result" class="mb-4" :meta="resultMeta" />

    <div class="workspace-grid">
      <section class="panel allocation-panel">
        <div class="panel-title">
          <h2>资产与权重</h2>
          <div class="panel-title-actions">
            <el-button v-if="result?.allocation?.length" size="small" text type="primary" @click="applyResultWeights">应用优化结果</el-button>
            <span>{{ assets.length }} 个标的</span>
          </div>
        </div>

        <el-alert
          v-if="mode === 'custom'"
          :type="Math.abs(customWeightTotal - 100) <= 0.5 ? 'success' : 'warning'"
          show-icon
          :closable="false"
          class="mb-3"
        >
          <template #default>
            <div class="weight-alert-content">
              <span>自定义权重合计 {{ customWeightTotal.toFixed(1) }}%，必须等于 100%</span>
              <div class="weight-actions">
                <el-button size="small" text @click="equalizeWeights">平均分配</el-button>
                <el-button size="small" text @click="normalizeCustomWeights">按当前比例归一化</el-button>
              </div>
            </div>
          </template>
        </el-alert>

        <el-table :data="allocationRows" size="small" :border="true" empty-text="请先添加资产">
          <el-table-column prop="symbol" label="标的" min-width="100" />
          <el-table-column label="自定义权重" min-width="130" align="right">
            <template #default="{ row }">
              <el-input-number
                v-model="customWeights[row.symbol]"
                :min="0"
                :max="100"
                :precision="1"
                :step="5"
                :disabled="mode !== 'custom'"
                controls-position="right"
                class="weight-input"
              />
            </template>
          </el-table-column>
          <el-table-column label="回测权重" min-width="110" align="right">
            <template #default="{ row }">
              <span class="weight-value">{{ formatPercent(row.finalWeight, { signed: false }) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section class="panel metric-panel">
        <div class="panel-title">
          <h2>核心指标</h2>
          <span>{{ modeLabel }}</span>
        </div>

          <div class="metrics-grid">
          <div v-for="item in metricCards" :key="item.label" class="metric-card">
            <span>{{ item.label }}</span>
            <strong :class="item.className">{{ item.value }}</strong>
          </div>
          <div v-if="result?.optimization" class="optimization-note">
            <strong>{{ result.optimization.label }}</strong>
            <span>{{ result.optimization.isInSample ? '基于历史样本寻找权重，存在样本内偏差' : '用于建立可比较的权重基线' }}</span>
            <span v-if="result.metrics?.fitCoefficient != null">拟合系数 {{ formatNumber(result.metrics.fitCoefficient, 3) }}（与 {{ result.benchmark }} 相关性）</span>
          </div>
        </div>
      </section>
    </div>

    <section class="panel chart-panel" v-if="result?.dates?.length">
      <div class="panel-title">
        <h2>净值曲线</h2>
        <span>组合 vs {{ result.benchmark }}</span>
      </div>
      <div ref="equityChartRef" class="chart"></div>
    </section>

    <section class="panel chart-panel" v-if="result?.dates?.length">
      <div class="panel-title">
        <h2>回撤曲线</h2>
        <span>最大回撤 {{ formatPercent(result.metrics?.maxDrawdown, { signed: false }) }}</span>
      </div>
      <div ref="drawdownChartRef" class="chart chart-small"></div>
    </section>

    <section class="panel assumptions-panel" v-if="result">
      <div class="panel-title">
        <h2>回测说明</h2>
        <span>{{ dataRangeText }}</span>
      </div>
      <div class="assumption-grid">
        <span><b>价格</b>{{ result.assumptions?.price || 'adjusted close' }}</span>
        <span><b>再平衡</b>{{ result.assumptions?.rebalance || '-' }}</span>
        <span><b>交易成本</b>{{ formatPercent(result.assumptions?.transactionCost || 0, { signed: false }) }}</span>
        <span><b>初始资金</b>{{ formatCompact(result.assumptions?.initialCapital, { currency: '$' }) }}</span>
      </div>
    </section>

    <div class="empty-state" v-if="!result && !running && !errorMessage">
      <StateBlock type="empty" title="添加资产后运行组合回测" description="默认可以从 AAPL、MSFT、NVDA、SPY、QQQ 等标的开始。" />
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { backtestPortfolio, getApiErrorMessage, searchSymbols } from '@/api'
import StateBlock from '@/components/common/StateBlock.vue'
import DataQualityBar from '@/components/common/DataQualityBar.vue'
import ModuleGuide from '@/components/common/ModuleGuide.vue'
import { formatCompact, formatNumber, formatPercent, valueClass } from '@/utils/formatters'

const selectedAsset = ref(null)
const searchResults = ref([])
const searchLoading = ref(false)
const assets = ref([
  { symbol: 'AAPL', name: 'Apple Inc.' },
  { symbol: 'MSFT', name: 'Microsoft Corp.' },
  { symbol: 'NVDA', name: 'NVIDIA Corp.' },
  { symbol: 'SPY', name: 'SPDR S&P 500 ETF' },
])
const customWeights = reactive({ AAPL: 25, MSFT: 25, NVDA: 25, SPY: 25 })
const period = ref('1y')
const mode = ref('equal')
const optimizationMode = ref('max_sharpe')
const benchmark = ref('SPY')
const running = ref(false)
const result = ref(null)
const resultMeta = ref({})
const errorMessage = ref('')
const equityChartRef = ref(null)
const drawdownChartRef = ref(null)
let equityChart = null
let drawdownChart = null
let searchTimer = null

const modeMap = { equal: '等权', custom: '自定义权重', risk_parity: '风险平价', min_variance: '最小方差', max_sharpe: '最大夏普' }
const modeLabel = computed(() => modeMap[mode.value] || mode.value)
const customWeightTotal = computed(() => assets.value.reduce((sum, asset) => sum + Number(customWeights[asset.symbol] || 0), 0))
const dataRangeText = computed(() => {
  const range = result.value?.dataRange
  if (!range) return '-'
  return `${formatShortDate(range.start)} - ${formatShortDate(range.end)} / ${range.observations}日`
})

const allocationRows = computed(() => {
  const finalMap = Object.fromEntries((result.value?.allocation || []).map(item => [item.symbol, item.weight]))
  return assets.value.map(asset => ({ symbol: asset.symbol, finalWeight: finalMap[asset.symbol] }))
})

const metricCards = computed(() => {
  const metrics = result.value?.metrics || {}
  return [
    { label: '总收益', value: formatPercent(metrics.totalReturn), className: valueClass(metrics.totalReturn) },
    { label: '年化收益', value: formatPercent(metrics.annualReturn), className: valueClass(metrics.annualReturn) },
    { label: '年化波动', value: formatPercent(metrics.annualVolatility, { signed: false }), className: '' },
    { label: '夏普比率', value: formatNumber(metrics.sharpeRatio), className: valueClass(metrics.sharpeRatio) },
    { label: '拟合系数', value: formatNumber(metrics.fitCoefficient, 3), className: '' },
    { label: '最大回撤', value: formatPercent(metrics.maxDrawdown, { signed: false }), className: 'text-down' },
    { label: '正收益日', value: formatPercent(metrics.positiveDays, { signed: false }), className: '' },
  ]
})

function searchAssets(q) {
  if (!q || q.trim().length < 1) {
    searchResults.value = []
    return
  }
  searchLoading.value = true
  clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    try {
      const res = await searchSymbols(q, 10)
      searchResults.value = res.data.results || []
    } catch {
      searchResults.value = []
    } finally {
      searchLoading.value = false
    }
  }, 300)
}

function addAsset(item) {
  if (!item?.symbol) return
  const symbol = item.symbol.toUpperCase()
  if (assets.value.some(asset => asset.symbol === symbol)) {
    selectedAsset.value = null
    return
  }
  assets.value.push({ symbol, name: item.name })
  customWeights[symbol] = 0
  selectedAsset.value = null
}

function removeAsset(symbol) {
  assets.value = assets.value.filter(asset => asset.symbol !== symbol)
  delete customWeights[symbol]
}

function equalizeWeights() {
  const weight = assets.value.length ? Number((100 / assets.value.length).toFixed(1)) : 0
  assets.value.forEach((asset, index) => {
    customWeights[asset.symbol] = index === assets.value.length - 1
      ? Number((100 - weight * Math.max(assets.value.length - 1, 0)).toFixed(1))
      : weight
  })
}

function normalizeCustomWeights() {
  if (customWeightTotal.value <= 0) {
    equalizeWeights()
    return
  }
  const total = customWeightTotal.value
  assets.value.forEach(asset => {
    customWeights[asset.symbol] = Number((Number(customWeights[asset.symbol] || 0) / total * 100).toFixed(1))
  })
  const roundedTotal = assets.value.reduce((sum, asset) => sum + Number(customWeights[asset.symbol] || 0), 0)
  if (assets.value.length) {
    const last = assets.value[assets.value.length - 1]
    customWeights[last.symbol] = Number((Number(customWeights[last.symbol] || 0) + 100 - roundedTotal).toFixed(1))
  }
}

function enableCustomWeights() {
  mode.value = 'custom'
  if (customWeightTotal.value <= 0) equalizeWeights()
}

async function calculateOptimal() {
  mode.value = optimizationMode.value
  await runBacktest()
}

function applyResultWeights() {
  const allocation = result.value?.allocation || []
  if (!allocation.length) return
  allocation.forEach(item => {
    customWeights[item.symbol] = Number((Number(item.weight || 0) * 100).toFixed(1))
  })
  mode.value = 'custom'
  normalizeCustomWeights()
  ElMessage.success('已将优化结果应用为可编辑权重')
}

function validateBacktest() {
  if (!assets.value.length) return 'ticker 不能为空'
  if (!benchmark.value?.trim()) return '基准不能为空'
  if (mode.value === 'custom' && Math.abs(customWeightTotal.value - 100) > 0.5) {
    return `自定义权重合计必须为 100%，当前为 ${customWeightTotal.value.toFixed(1)}%`
  }
  return ''
}

async function runBacktest() {
  const validation = validateBacktest()
  if (validation) {
    errorMessage.value = validation
    ElMessage.warning(validation)
    return
  }

  running.value = true
  errorMessage.value = ''
  try {
    const weights = {}
    for (const asset of assets.value) weights[asset.symbol] = Number(customWeights[asset.symbol] || 0)
    const res = await backtestPortfolio({
      symbols: assets.value.map(asset => asset.symbol),
      period: period.value,
      mode: mode.value,
      weights,
      benchmark: benchmark.value.trim().toUpperCase(),
    })
    result.value = res.data
    resultMeta.value = res.meta || {}
    await nextTick()
    renderCharts()
  } catch (e) {
    errorMessage.value = getApiErrorMessage(e, '组合回测失败')
    ElMessage.error(errorMessage.value)
  } finally {
    running.value = false
  }
}

function renderCharts() {
  renderEquityChart()
  renderDrawdownChart()
}

function renderEquityChart() {
  if (!equityChartRef.value || !result.value) return
  if (!equityChart) equityChart = echarts.init(equityChartRef.value, 'dark')
  const dates = result.value.dates.map(formatShortDate)
  const series = [{ name: '组合', type: 'line', data: safeSeries(result.value.equity, 100), smooth: true, symbol: 'none', lineStyle: { color: '#4a8eff', width: 2 } }]
  if (result.value.benchmarkSeries?.equity?.length) {
    series.push({ name: result.value.benchmarkSeries.symbol, type: 'line', data: safeSeries(result.value.benchmarkSeries.equity, 100), smooth: true, symbol: 'none', lineStyle: { color: '#ffab00', width: 2 } })
  }
  equityChart.setOption(baseLineOption(dates, series, '{value}'), true)
}

function renderDrawdownChart() {
  if (!drawdownChartRef.value || !result.value) return
  if (!drawdownChart) drawdownChart = echarts.init(drawdownChartRef.value, 'dark')
  const dates = result.value.dates.map(formatShortDate)
  const series = [{ name: '组合回撤', type: 'line', data: safeSeries(result.value.drawdown, 100), smooth: true, symbol: 'none', areaStyle: { color: 'rgba(255, 23, 68, 0.14)' }, lineStyle: { color: '#ff1744', width: 2 } }]
  drawdownChart.setOption(baseLineOption(dates, series, '{value}%'), true)
}

function safeSeries(values, multiplier = 1) {
  return (values || []).map(value => Number.isFinite(Number(value)) ? Number((Number(value) * multiplier).toFixed(2)) : null)
}

function baseLineOption(dates, series, yFormatter) {
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: '#1e2130', borderColor: '#2a2e3e', textStyle: { color: '#e8eaed', fontSize: 12 } },
    legend: { top: 0, textStyle: { color: '#9aa0a6' } },
    grid: { left: '3%', right: '3%', top: 36, bottom: 28 },
    xAxis: { type: 'category', data: dates, axisLine: { lineStyle: { color: '#2a2e3e' } }, axisLabel: { color: '#9aa0a6', fontSize: 10 } },
    yAxis: { type: 'value', axisLabel: { color: '#9aa0a6', formatter: yFormatter }, splitLine: { lineStyle: { color: '#1e2130' } } },
    series,
  }
}

function formatShortDate(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function getTypeLabel(type) {
  const map = { stock: '股票', etf: 'ETF', index: '指数', future: '期货', forex: '外汇', crypto: '加密' }
  return map[type] || type || ''
}

function handleResize() {
  equityChart?.resize()
  drawdownChart?.resize()
}

onMounted(() => window.addEventListener('resize', handleResize))
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  equityChart?.dispose()
  drawdownChart?.dispose()
})
</script>

<style lang="scss" scoped>
.portfolio-page { max-width: 1440px; margin: 0 auto; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; gap: 12px; }
.page-header h1 { font-size: 22px; font-weight: 700; color: $text-primary; margin-bottom: 4px; }
.page-header p { font-size: 14px; color: $text-secondary; }
.control-panel, .panel { background-color: $bg-card; border: 1px solid $border-color; border-radius: $radius-lg; }
.control-panel { padding: 16px 20px; margin-bottom: 20px; }
.search-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.allocation-toolbar { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-top: 14px; padding-top: 14px; border-top: 1px solid $border-color; }
.toolbar-label { color: $text-primary; font-size: 13px; font-weight: 700; }
.optimization-select { width: 112px; }
.toolbar-hint { color: $text-muted; font-size: 12px; }
.asset-search { flex: 1; min-width: 280px; }
.small-select { width: 120px; }
.mode-select { width: 150px; }
.benchmark-input { width: 100px; }
.search-option { display: flex; align-items: center; gap: 10px; width: 100%; }
.opt-symbol { font-weight: 700; color: $color-accent; min-width: 70px; }
.opt-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.asset-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.workspace-grid { display: grid; grid-template-columns: minmax(420px, 0.9fr) minmax(420px, 1.1fr); gap: 20px; margin-bottom: 20px; }
.panel { padding: 16px; }
.panel-title { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
.panel-title h2 { color: $text-primary; font-size: 15px; font-weight: 700; margin: 0; }
.panel-title span { color: $text-muted; font-size: 12px; }
.panel-title-actions { display: flex; align-items: center; gap: 8px; }
.weight-input { width: 110px; }
.weight-alert-content { display: flex; align-items: center; justify-content: space-between; gap: 12px; width: 100%; }
.weight-actions { display: flex; gap: 4px; flex-wrap: wrap; }
.weight-value { color: $text-primary; font-weight: 600; }
.metrics-grid { display: grid; grid-template-columns: repeat(3, minmax(120px, 1fr)); gap: 12px; }
.metric-card { min-height: 72px; padding: 12px; border: 1px solid $border-color; border-radius: $radius-md; background-color: $bg-secondary; display: flex; flex-direction: column; justify-content: space-between; }
.metric-card span { color: $text-muted; font-size: 12px; }
.metric-card strong { color: $text-primary; font-size: 20px; font-weight: 700; font-variant-numeric: tabular-nums; }
.optimization-note { display: flex; flex-wrap: wrap; gap: 8px 16px; margin-top: 14px; padding-top: 12px; border-top: 1px solid $border-color; color: $text-muted; font-size: 12px; }
.optimization-note strong { color: $color-accent-light; }
.chart-panel { margin-bottom: 20px; }
.chart { width: 100%; height: 420px; }
.chart-small { height: 280px; }
.empty-state { padding: 20px 0; }
.assumption-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; color: $text-secondary; font-size: 13px; }
.assumption-grid b { color: $text-muted; margin-right: 6px; font-weight: 500; }
@media (max-width: 1100px) { .workspace-grid { grid-template-columns: 1fr; } }
</style>
