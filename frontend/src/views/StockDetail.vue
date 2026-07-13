<template>
  <div class="stock-detail">
    <StateBlock
      v-if="store.stockError && !store.stockLoading"
      type="error"
      title="资产信息加载失败"
      :description="store.stockError"
    >
      <template #action>
        <el-button size="small" @click="loadData">重试</el-button>
        <el-button size="small" @click="$router.push('/')">返回市场</el-button>
      </template>
    </StateBlock>

    <template v-else-if="store.currentStock">
      <StockInfoCard :stock="store.currentStock" />
      <ModuleGuide title="资产详情" description="用来核对单个股票、ETF、指数或商品的价格和风险信息。" :steps="['先查看资产名称、交易所、币种和数据说明。', '用 K 线时间范围观察价格与成交量。', '结合收益、波动率和最大回撤，再进入组合或对比模块。']" note="图表和指标是历史数据描述，不是未来预测。" class="mt-4" />

      <div class="action-bar">
        <el-button type="primary" plain>加入自选</el-button>
        <el-button plain @click="$router.push('/portfolio')">加入组合</el-button>
        <el-button plain disabled>模拟买入</el-button>
        <el-button plain @click="$router.push('/compare')">加入对比</el-button>
      </div>

      <DataQualityBar
        class="mt-4"
        :meta="mergedMeta"
        :currency="store.currentStock.currency"
        :exchange="store.currentStock.exchange"
      />

      <div class="metric-grid mt-4">
        <div v-for="metric in returnMetrics" :key="metric.label" class="metric-card">
          <span>{{ metric.label }}</span>
          <strong :class="valueClass(metric.value)">{{ formatPercent(metric.value) }}</strong>
        </div>
        <div class="metric-card">
          <span>年化波动</span>
          <strong>{{ formatPercent(riskMetrics.annualVolatility, { signed: false }) }}</strong>
        </div>
        <div class="metric-card">
          <span>最大回撤</span>
          <strong class="text-down">{{ formatPercent(riskMetrics.maxDrawdown, { signed: false }) }}</strong>
        </div>
      </div>

      <StateBlock
        v-if="store.historyError"
        type="error"
        title="K 线加载失败"
        :description="store.historyError"
        class="mt-4"
      />

      <div class="chart-section mt-4">
        <StockChart
          :data="store.historyData"
          :loading="store.historyLoading"
          :symbol="store.currentStock.symbol"
          @change-interval="handleIntervalChange"
        />
      </div>

      <div class="financials-section mt-4">
        <FinancialTable :symbol="store.currentStock.symbol" />
      </div>
    </template>

    <StateBlock
      v-else-if="store.stockLoading"
      type="loading"
      title="正在加载资产信息"
      description="正在请求资产基础信息和历史行情。"
    />

    <StateBlock
      v-else
      type="empty"
      title="未找到该资产"
      description="请检查 ticker 是否正确，或从市场首页重新搜索。"
    >
      <template #action>
        <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
      </template>
    </StateBlock>
  </div>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useStockStore } from '@/store/stockStore'
import StockInfoCard from '@/components/stock/StockInfoCard.vue'
import StockChart from '@/components/stock/StockChart.vue'
import FinancialTable from '@/components/stock/FinancialTable.vue'
import StateBlock from '@/components/common/StateBlock.vue'
import DataQualityBar from '@/components/common/DataQualityBar.vue'
import ModuleGuide from '@/components/common/ModuleGuide.vue'
import { formatPercent, valueClass } from '@/utils/formatters'

const route = useRoute()
const store = useStockStore()
let currentPeriod = '1y'

const mergedMeta = computed(() => ({
  ...store.stockMeta,
  warnings: [
    ...(store.stockMeta?.warnings || []),
    ...(store.historyMeta?.warnings || []),
  ],
}))

const closes = computed(() => (store.historyData || [])
  .map(item => Number(item.close))
  .filter(value => Number.isFinite(value) && value > 0))

const returnMetrics = computed(() => [
  { label: '近1周', value: periodReturn(5) },
  { label: '近1月', value: periodReturn(21) },
  { label: '近3月', value: periodReturn(63) },
  { label: '近1年', value: periodReturn(252) },
])

const riskMetrics = computed(() => {
  if (closes.value.length < 2) return { annualVolatility: null, maxDrawdown: null }
  const returns = []
  for (let i = 1; i < closes.value.length; i += 1) {
    returns.push(closes.value[i] / closes.value[i - 1] - 1)
  }
  const mean = returns.reduce((sum, item) => sum + item, 0) / returns.length
  const variance = returns.reduce((sum, item) => sum + ((item - mean) ** 2), 0) / Math.max(returns.length - 1, 1)
  let peak = closes.value[0]
  let maxDrawdown = 0
  closes.value.forEach(price => {
    peak = Math.max(peak, price)
    maxDrawdown = Math.min(maxDrawdown, price / peak - 1)
  })
  return {
    annualVolatility: Math.sqrt(variance) * Math.sqrt(252),
    maxDrawdown,
  }
})

function periodReturn(days) {
  if (closes.value.length < 2) return null
  const end = closes.value[closes.value.length - 1]
  const startIndex = Math.max(0, closes.value.length - 1 - days)
  const start = closes.value[startIndex]
  if (!start) return null
  return end / start - 1
}

async function loadData() {
  const symbol = route.params.symbol
  if (!symbol) return
  await store.fetchStockInfo(symbol)
  await store.fetchStockHistory(symbol, currentPeriod, '1d')
}

function handleIntervalChange(period) {
  currentPeriod = period
  const symbol = route.params.symbol
  if (symbol) store.fetchStockHistory(symbol, period, '1d')
}

onMounted(loadData)
watch(() => route.params.symbol, loadData)
</script>

<style lang="scss" scoped>
.stock-detail {
  max-width: 1400px;
  margin: 0 auto;
}

.action-bar {
  margin-top: 12px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
}

.metric-card {
  min-height: 76px;
  padding: 13px 14px;
  background: $bg-card;
  border: 1px solid $border-color;
  border-radius: $radius-md;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.metric-card span {
  color: $text-muted;
  font-size: 12px;
}

.metric-card strong {
  color: $text-primary;
  font-size: 20px;
  font-variant-numeric: tabular-nums;
}

.chart-section,
.financials-section {
  margin-bottom: 16px;
}
</style>
