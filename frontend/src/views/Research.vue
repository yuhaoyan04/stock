<template>
  <div class="research-page">
    <div class="page-header">
      <div>
        <h1>研究组合</h1>
        <p>查看公开持仓模板、权重结构和与 SPY / QQQ 的走势参考，不构成跟投建议。</p>
      </div>
      <el-select v-model="selectedId" class="portfolio-select" @change="loadPortfolio">
        <el-option v-for="item in portfolios" :key="item.id" :label="item.name" :value="item.id" />
      </el-select>
    </div>
    <ModuleGuide title="研究组合" description="查看公开持仓模板、权重结构和历史参考，不将其理解为实时持仓或跟投建议。" :steps="['选择研究组合并核对披露日期。', '查看权重和底层持仓。', '用走势参考与基准对比，注意公开披露具有滞后性。']" class="mb-4" />

    <StateBlock v-if="errorMessage" type="error" title="研究组合加载失败" :description="errorMessage" class="mb-4">
      <template #action>
        <el-button size="small" @click="loadInitial">重试</el-button>
      </template>
    </StateBlock>

    <template v-if="portfolio">
      <el-alert
        title="公开持仓或 13F 类数据通常存在披露延迟。本页用于研究工作流演示，不构成买卖或跟投建议。"
        type="warning"
        show-icon
        :closable="false"
        class="mb-4"
      />

      <DataQualityBar class="mb-4" :meta="meta" />

      <section class="profile-panel">
        <div>
          <p class="eyebrow">{{ portfolio.manager }}</p>
          <h2>{{ portfolio.name }}</h2>
          <p>{{ portfolio.description }}</p>
        </div>
        <div class="profile-facts">
          <span><b>数据来源</b>{{ portfolio.source }}</span>
          <span><b>披露日期</b>{{ portfolio.disclosureDate }}</span>
          <span><b>持仓截至</b>{{ portfolio.asOfDate }}</span>
          <span><b>持仓数量</b>{{ portfolio.holdings?.length || 0 }}</span>
        </div>
      </section>

      <div class="workspace-grid mt-4">
        <section class="panel chart-panel">
          <div class="panel-title">
            <h2>权重分布</h2>
            <span>合计 {{ formatPercent(portfolio.totalWeight, { signed: false }) }}</span>
          </div>
          <div ref="weightChartRef" class="chart chart-small"></div>
        </section>

        <section class="panel chart-panel">
          <div class="panel-title">
            <h2>走势参考</h2>
            <div class="period-control">
              <el-select v-model="comparePeriod" size="small" @change="loadComparison">
                <el-option label="3个月" value="3mo" />
                <el-option label="6个月" value="6mo" />
                <el-option label="1年" value="1y" />
                <el-option label="2年" value="2y" />
                <el-option label="5年" value="5y" />
              </el-select>
            </div>
          </div>
          <div v-loading="compareLoading" ref="compareChartRef" class="chart chart-small"></div>
          <StateBlock
            v-if="!compareLoading && compareError"
            type="warning"
            title="对比数据暂不可用"
            :description="compareError"
            compact
          />
        </section>
      </div>

      <section class="panel holdings-panel mt-4">
        <div class="panel-title">
          <h2>公开持仓</h2>
          <span>按模板权重排序</span>
        </div>
        <el-table :data="portfolio.holdings || []" size="small" border>
          <el-table-column label="Ticker" width="100">
            <template #default="{ row }">
              <span class="symbol-cell" @click="goToStock(row.symbol)">{{ row.symbol }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="名称" min-width="180" show-overflow-tooltip />
          <el-table-column prop="sector" label="行业" min-width="150" show-overflow-tooltip />
          <el-table-column label="权重" width="120" align="right" sortable>
            <template #default="{ row }">{{ formatPercent(row.weight, { signed: false }) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center">
            <template #default="{ row }">
              <el-button size="small" text type="primary" @click="goToStock(row.symbol)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </template>

    <StateBlock v-else-if="loading" type="loading" title="正在加载研究组合" description="正在读取公开持仓模板。" />
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { compareResearchPortfolio, getApiErrorMessage, getResearchPortfolio, getResearchPortfolios } from '@/api'
import DataQualityBar from '@/components/common/DataQualityBar.vue'
import ModuleGuide from '@/components/common/ModuleGuide.vue'
import StateBlock from '@/components/common/StateBlock.vue'
import { formatPercent } from '@/utils/formatters'

const router = useRouter()
const portfolios = ref([])
const selectedId = ref('')
const portfolio = ref(null)
const meta = ref({})
const loading = ref(false)
const errorMessage = ref('')
const comparePeriod = ref('1y')
const compareLoading = ref(false)
const compareError = ref('')
const weightChartRef = ref(null)
const compareChartRef = ref(null)
let weightChart = null
let compareChart = null

const colors = ['#4a8eff', '#00c853', '#ffab00', '#ff1744', '#29b6f6', '#e040fb', '#76ff03', '#ff6d00', '#8b9cff', '#00bfa5']

async function loadInitial() {
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await getResearchPortfolios()
    portfolios.value = res.data.portfolios || []
    selectedId.value = selectedId.value || portfolios.value[0]?.id || ''
    if (selectedId.value) await loadPortfolio(selectedId.value)
  } catch (e) {
    errorMessage.value = getApiErrorMessage(e, '研究组合列表加载失败')
  } finally {
    loading.value = false
  }
}

async function loadPortfolio(id = selectedId.value) {
  if (!id) return
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await getResearchPortfolio(id)
    portfolio.value = res.data
    meta.value = res.meta || {}
    await nextTick()
    renderWeightChart()
    await loadComparison()
  } catch (e) {
    errorMessage.value = getApiErrorMessage(e, '研究组合详情加载失败')
    portfolio.value = null
  } finally {
    loading.value = false
  }
}

async function loadComparison() {
  if (!selectedId.value) return
  compareLoading.value = true
  compareError.value = ''
  try {
    const res = await compareResearchPortfolio(selectedId.value, comparePeriod.value)
    await nextTick()
    renderCompareChart(res.data.comparison || {})
  } catch (e) {
    compareError.value = getApiErrorMessage(e, '走势参考加载失败')
  } finally {
    compareLoading.value = false
  }
}

function renderWeightChart() {
  if (!weightChartRef.value || !portfolio.value) return
  if (!weightChart) weightChart = echarts.init(weightChartRef.value, 'dark')
  const data = (portfolio.value.holdings || []).map((item, index) => ({
    name: item.symbol,
    value: Number((item.weight * 100).toFixed(2)),
    itemStyle: { color: colors[index % colors.length] },
  }))
  weightChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', formatter: '{b}: {c}%', backgroundColor: '#1e2130', borderColor: '#2a2e3e', textStyle: { color: '#e8eaed' } },
    legend: { type: 'scroll', bottom: 0, textStyle: { color: '#9aa0a6' } },
    series: [{ type: 'pie', radius: ['48%', '72%'], center: ['50%', '45%'], data, label: { color: '#e8eaed', formatter: '{b}\n{c}%' } }],
  }, true)
}

function renderCompareChart(comparison) {
  if (!compareChartRef.value) return
  if (!compareChart) compareChart = echarts.init(compareChartRef.value, 'dark')
  const dates = (comparison.dates || []).map(value => {
    const date = new Date(value)
    return Number.isNaN(date.getTime()) ? '-' : date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  })
  const series = Object.entries(comparison.series || {}).map(([symbol, values], index) => ({
    name: symbol,
    type: 'line',
    data: (values || []).map(value => Number.isFinite(Number(value)) ? Number(value) : null),
    smooth: true,
    symbol: 'none',
    lineStyle: { color: colors[index % colors.length], width: symbol === 'SPY' || symbol === 'QQQ' ? 3 : 1.8 },
  }))
  compareChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: '#1e2130', borderColor: '#2a2e3e', textStyle: { color: '#e8eaed' } },
    legend: { top: 0, textStyle: { color: '#9aa0a6' } },
    grid: { left: '3%', right: '4%', top: 38, bottom: 30 },
    xAxis: { type: 'category', data: dates, axisLine: { lineStyle: { color: '#2a2e3e' } }, axisLabel: { color: '#9aa0a6', fontSize: 10 } },
    yAxis: { type: 'value', axisLabel: { color: '#9aa0a6', formatter: '{value}' }, splitLine: { lineStyle: { color: '#1e2130' } } },
    series,
  }, true)
}

function goToStock(symbol) {
  router.push(`/stock/${encodeURIComponent(symbol)}`)
}

function handleResize() {
  weightChart?.resize()
  compareChart?.resize()
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  loadInitial()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  weightChart?.dispose()
  compareChart?.dispose()
})
</script>

<style lang="scss" scoped>
.research-page { max-width: 1440px; margin: 0 auto; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 18px; }
.page-header h1 { color: $text-primary; font-size: 22px; margin-bottom: 4px; }
.page-header p { color: $text-secondary; font-size: 14px; }
.portfolio-select { width: 360px; }
.profile-panel, .panel { background: $bg-card; border: 1px solid $border-color; border-radius: $radius-lg; }
.profile-panel { padding: 18px; display: grid; grid-template-columns: minmax(0, 1fr) minmax(320px, 0.6fr); gap: 18px; }
.eyebrow { color: $color-accent; font-size: 12px; font-weight: 700; text-transform: uppercase; margin-bottom: 6px; }
.profile-panel h2 { color: $text-primary; font-size: 20px; margin-bottom: 8px; }
.profile-panel p { color: $text-secondary; line-height: 1.6; }
.profile-facts { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.profile-facts span { display: flex; flex-direction: column; gap: 4px; color: $text-primary; font-size: 13px; background: $bg-secondary; border: 1px solid $border-color; border-radius: $radius-md; padding: 10px; }
.profile-facts b { color: $text-muted; font-size: 12px; font-weight: 500; }
.workspace-grid { display: grid; grid-template-columns: minmax(420px, 0.8fr) minmax(520px, 1.2fr); gap: 16px; }
.panel { padding: 16px; }
.panel-title { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.panel-title h2 { color: $text-primary; font-size: 16px; font-weight: 700; }
.panel-title span { color: $text-muted; font-size: 12px; }
.period-control { width: 110px; }
.chart { width: 100%; height: 360px; }
.chart-small { height: 340px; }
.symbol-cell { color: $color-accent; font-weight: 700; cursor: pointer; }
.symbol-cell:hover { color: $color-accent-light; }
@media (max-width: 1100px) { .workspace-grid, .profile-panel { grid-template-columns: 1fr; } .portfolio-select { width: 260px; } }
</style>
