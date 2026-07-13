<template>
  <div class="compare-page">
    <div class="page-header">
      <h1>多资产对比</h1>
      <p>添加多只股票/ETF/指数，对比走势表现（百分比归化）</p>
    </div>

    <!-- 搜索添加区 -->
    <div class="search-section">
      <div class="search-row">
        <el-select
          v-model="selectedStock"
          filterable
          remote
          reserve-keyword
          placeholder="搜索并添加对比标的..."
          :remote-method="searchStocks"
          :loading="searchLoading"
          clearable
          value-key="symbol"
          class="compare-search"
          @change="addSymbol"
        >
          <el-option
            v-for="item in searchResults"
            :key="item.symbol"
            :label="item.symbol"
            :value="item"
          >
            <div class="search-option">
              <span class="opt-symbol">{{ item.symbol }}</span>
              <span class="opt-name">{{ item.name }}</span>
              <el-tag size="small">{{ getTypeLabel(item.type) }}</el-tag>
            </div>
          </el-option>
        </el-select>

        <el-select v-model="comparePeriod" size="default" style="width: 140px" @change="doCompare">
          <el-option label="1个月" value="1mo" />
          <el-option label="3个月" value="3mo" />
          <el-option label="6个月" value="6mo" />
          <el-option label="1年" value="1y" />
          <el-option label="2年" value="2y" />
          <el-option label="5年" value="5y" />
        </el-select>

        <el-button type="primary" @click="doCompare" :loading="comparing" :disabled="symbols.length < 2">
          对比 ({{ symbols.length }})
        </el-button>
      </div>

      <!-- 已选标的 -->
      <div class="selected-tags" v-if="symbols.length > 0">
        <el-tag
          v-for="(sym, i) in symbols"
          :key="sym"
          closable
          :disable-transitions="false"
          @close="removeSymbol(i)"
          size="large"
          class="compare-tag"
        >
          {{ sym }}
        </el-tag>
      </div>
    </div>

    <!-- 对比图表 -->
    <div class="chart-section" v-if="compareData.dates?.length > 0">
      <div ref="compareChartRef" class="compare-chart"></div>
    </div>

    <!-- 对比表格 -->
    <div class="table-section mt-4" v-if="compareData.dates?.length > 0">
      <el-table :data="tableData" :border="true" :stripe="true" size="small">
        <el-table-column prop="metric" label="指标" width="140" fixed="left" />
        <el-table-column
          v-for="sym in symbols"
          :key="sym"
          :label="sym"
          :prop="sym"
          align="right"
          min-width="120"
        >
          <template #default="{ row }">
            <span :class="getCellClass(row.metric, row[sym])">
              {{ row[sym] || '—' }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 空状态 -->
    <div class="empty-state" v-else-if="!comparing">
      <el-empty description="请添加至少 2 个标的进行对比" :image-size="100">
        <p class="empty-hint">搜索并添加股票代码，选择时间范围后点击"对比"</p>
      </el-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { searchSymbols, compareSymbols, getStockInfo } from '@/api'

const selectedStock = ref(null)
const searchResults = ref([])
const searchLoading = ref(false)
const symbols = ref([])
const comparePeriod = ref('1y')
const comparing = ref(false)
const compareData = ref({ dates: [], series: {} })
const compareChartRef = ref(null)
let chart = null

// 搜索结果防抖
let searchTimer = null
function searchStocks(q) {
  if (!q || q.trim().length < 1) {
    searchResults.value = []
    return
  }
  searchLoading.value = true
  clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    try {
      const res = await searchSymbols(q, 10)
      searchResults.value = res.data.results
    } catch {
      searchResults.value = []
    } finally {
      searchLoading.value = false
    }
  }, 300)
}

function addSymbol(item) {
  if (!item?.symbol) return
  if (symbols.value.includes(item.symbol)) {
    selectedStock.value = null
    return
  }
  if (symbols.value.length >= 10) {
    return
  }
  symbols.value.push(item.symbol)
  selectedStock.value = null
}

function removeSymbol(index) {
  symbols.value.splice(index, 1)
}

async function doCompare() {
  if (symbols.value.length < 2) return
  comparing.value = true
  try {
    const res = await compareSymbols(symbols.value, comparePeriod.value)
    compareData.value = res.data
    await nextTick()
    renderCompareChart()
  } catch (e) {
    console.error('Compare failed:', e)
  } finally {
    comparing.value = false
  }
}

// 颜色调色板
const colors = ['#4a8eff', '#00c853', '#ffab00', '#ff1744', '#e040fb', '#00e5ff', '#ff6d00', '#76ff03', '#2979ff', '#ff4081']

function renderCompareChart() {
  if (!compareChartRef.value) return
  if (!chart) {
    chart = echarts.init(compareChartRef.value, 'dark')
  }

  const { dates, series } = compareData.value
  if (!dates || dates.length === 0) return

  const chartSeries = Object.entries(series).map(([sym, data], i) => ({
    name: sym,
    type: 'line',
    data,
    smooth: true,
    symbol: 'none',
    lineStyle: { color: colors[i % colors.length], width: 2 },
    itemStyle: { color: colors[i % colors.length] },
  }))

  chart.setOption({
    backgroundColor: 'transparent',
    title: {
      text: '走势对比 (起始日=100)',
      left: 'center',
      textStyle: { color: '#9aa0a6', fontSize: 13, fontWeight: 'normal' },
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1e2130',
      borderColor: '#2a2e3e',
      textStyle: { color: '#e8eaed', fontSize: 12 },
      formatter(params) {
        let html = `<div style="font-weight:600;margin-bottom:4px">${params[0]?.axisValue || ''}</div>`
        params.forEach(p => {
          html += `<div style="display:flex;align-items:center;gap:6px;margin:2px 0">
            <span style="width:8px;height:8px;border-radius:50%;background:${p.color};display:inline-block"></span>
            ${p.seriesName}: <b>${p.value?.toFixed(2)}%</b>
          </div>`
        })
        return html
      },
    },
    legend: {
      data: Object.keys(series),
      bottom: 0,
      textStyle: { color: '#9aa0a6', fontSize: 12 },
    },
    grid: {
      left: '3%', right: '3%', top: '12%', bottom: '10%',
    },
    xAxis: {
      type: 'category',
      data: dates.map(d => {
        const dt = new Date(d)
        return dt.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
      }),
      axisLine: { lineStyle: { color: '#2a2e3e' } },
      axisLabel: { color: '#9aa0a6', fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#9aa0a6',
        formatter: '{value}%',
      },
      splitLine: { lineStyle: { color: '#1e2130' } },
    },
    series: chartSeries,
  }, true)
}

function handleResize() {
  chart?.resize()
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})

// 对比表格数据
const tableData = computed(() => {
  const { series } = compareData.value
  if (Object.keys(series).length === 0) return []

  const symList = Object.keys(series)
  const rows = [
    { metric: '起始值', ...Object.fromEntries(symList.map(s => [s, '100.00%'])) },
  ]

  // 最新值
  const latestRow = { metric: '最新值' }
  symList.forEach(s => {
    const data = series[s]
    if (data && data.length > 0) {
      const last = data[data.length - 1]
      const change = last - 100
      const sign = change >= 0 ? '+' : ''
      latestRow[s] = `${sign}${change.toFixed(2)}%`
    } else {
      latestRow[s] = '—'
    }
  })
  rows.push(latestRow)

  return rows
})

function getCellClass(metric, value) {
  if (metric !== '最新值' || !value || value === '—') return ''
  return value.startsWith('+') ? 'text-up' : 'text-down'
}

function getTypeLabel(type) {
  const map = { stock: '股票', etf: 'ETF', index: '指数', future: '期货', forex: '外汇', crypto: '加密' }
  return map[type] || type || ''
}

import { computed } from 'vue'
</script>

<style lang="scss" scoped>
.compare-page {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;

  h1 {
    font-size: 22px;
    font-weight: 700;
    color: $text-primary;
    margin-bottom: 4px;
  }

  p {
    font-size: 14px;
    color: $text-secondary;
  }
}

.search-section {
  background-color: $bg-card;
  border: 1px solid $border-color;
  border-radius: $radius-lg;
  padding: 16px 20px;
  margin-bottom: 20px;
}

.search-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.compare-search {
  flex: 1;
  max-width: 400px;
}

.search-option {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.opt-symbol {
  font-weight: 700;
  color: $color-accent;
  min-width: 60px;
}

.opt-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.compare-tag {
  font-size: 13px;
}

.compare-chart {
  width: 100%;
  height: 420px;
}

.chart-section {
  background-color: $bg-card;
  border: 1px solid $border-color;
  border-radius: $radius-lg;
  padding: 16px;
}

.table-section {
  background-color: $bg-card;
  border: 1px solid $border-color;
  border-radius: $radius-lg;
  padding: 16px;
}

.empty-state {
  padding: 60px 0;
}

.empty-hint {
  font-size: 13px;
  color: $text-muted;
  margin-top: 8px;
}
</style>
