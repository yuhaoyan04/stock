<template>
  <div class="stock-chart-wrapper">
    <div class="chart-toolbar">
      <div>
        <strong>{{ symbol }}</strong>
        <span>价格与成交量</span>
      </div>
      <div class="time-frames">
        <el-radio-group v-model="selectedInterval" size="small" @change="changeInterval">
          <el-radio-button value="1d">1日</el-radio-button>
          <el-radio-button value="5d">5日</el-radio-button>
          <el-radio-button value="1mo">1月</el-radio-button>
          <el-radio-button value="3mo">3月</el-radio-button>
          <el-radio-button value="6mo">6月</el-radio-button>
          <el-radio-button value="1y">1年</el-radio-button>
          <el-radio-button value="5y">5年</el-radio-button>
          <el-radio-button value="max">全部</el-radio-button>
        </el-radio-group>
      </div>
      <el-button-group size="small">
        <el-button :type="chartType === 'candle' ? 'primary' : 'default'" @click="chartType = 'candle'">K线</el-button>
        <el-button :type="chartType === 'line' ? 'primary' : 'default'" @click="chartType = 'line'">折线</el-button>
      </el-button-group>
    </div>
    <div v-loading="loading" class="chart-body">
      <StateBlock
        v-if="!loading && !data.length"
        type="empty"
        title="暂无 K 线数据"
        description="当前标的或时间范围没有返回有效 OHLCV 数据。"
      />
      <div v-show="data.length" ref="chartRef" class="chart-container"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import StateBlock from '@/components/common/StateBlock.vue'
import { formatCompact, formatNumber } from '@/utils/formatters'

const props = defineProps({
  data: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  symbol: { type: String, default: '' },
})

const emit = defineEmits(['change-interval'])

const chartRef = ref(null)
const selectedInterval = ref('1mo')
const chartType = ref('candle')
let chart = null

const upColor = '#00c853'
const downColor = '#ff1744'

function formatData() {
  const rawData = (props.data || []).filter(d => [d.open, d.high, d.low, d.close].every(v => Number.isFinite(Number(v))))
  if (rawData.length === 0) return { dates: [], ohlc: [], volumes: [] }

  const dates = rawData.map(d => {
    const dt = new Date(d.date)
    if (rawData.length > 80) return dt.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
    return dt.toLocaleDateString('zh-CN')
  })

  const ohlc = rawData.map(d => [Number(d.open), Number(d.close), Number(d.low), Number(d.high)])
  const volumes = rawData.map(d => ({
    value: Number(d.volume || 0),
    itemStyle: { color: Number(d.close) >= Number(d.open) ? `${upColor}66` : `${downColor}66` },
  }))

  return { dates, ohlc, volumes }
}

async function renderChart() {
  await nextTick()
  if (!chartRef.value || !props.data.length) return
  if (!chart) chart = echarts.init(chartRef.value, 'dark')

  const { dates, ohlc, volumes } = formatData()
  if (!dates.length) return

  const priceSeries = chartType.value === 'candle'
    ? [{
        name: 'K线',
        type: 'candlestick',
        data: ohlc,
        itemStyle: { color: upColor, color0: downColor, borderColor: upColor, borderColor0: downColor },
        barWidth: '60%',
      }]
    : [{
        name: '收盘价',
        type: 'line',
        data: ohlc.map(d => d[1]),
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#4a8eff', width: 2 },
        areaStyle: { color: 'rgba(74, 142, 255, 0.12)' },
      }]

  chart.setOption({
    backgroundColor: 'transparent',
    grid: [
      { left: '3%', right: '3%', top: 24, height: '62%' },
      { left: '3%', right: '3%', top: '76%', height: '16%' },
    ],
    xAxis: [
      { type: 'category', data: dates, axisLine: { lineStyle: { color: '#2a2e3e' } }, axisTick: { show: false }, axisLabel: { color: '#9aa0a6', fontSize: 11 } },
      { type: 'category', data: dates, gridIndex: 1, axisLine: { lineStyle: { color: '#2a2e3e' } }, axisTick: { show: false }, axisLabel: { show: false } },
    ],
    yAxis: [
      { scale: true, splitLine: { lineStyle: { color: '#1e2130' } }, axisLabel: { color: '#9aa0a6', formatter: value => formatNumber(value, 2) } },
      { scale: true, gridIndex: 1, splitLine: { show: false }, axisLabel: { show: false } },
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 0, end: 100 },
    ],
    series: [
      ...priceSeries,
      { name: '成交量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1, data: volumes, barWidth: '60%' },
    ],
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: '#1e2130',
      borderColor: '#2a2e3e',
      textStyle: { color: '#e8eaed', fontSize: 12 },
      formatter(params) {
        const date = params?.[0]?.axisValue || ''
        const candle = params.find(p => p.seriesName === 'K线' || p.seriesName === '收盘价')
        const vol = params.find(p => p.seriesName === '成交量')
        let html = `<div style="font-weight:600;margin-bottom:6px">${date}</div>`
        if (candle?.seriesName === 'K线') {
          const [open, close, low, high] = candle.data
          html += `开: ${formatNumber(open, 2)}<br/>高: ${formatNumber(high, 2)}<br/>低: ${formatNumber(low, 2)}<br/>收: ${formatNumber(close, 2)}`
        } else if (candle?.data !== undefined) {
          html += `收盘: ${formatNumber(candle.data, 2)}`
        }
        if (vol?.data?.value !== undefined) html += `<br/>量: ${formatCompact(vol.data.value)}`
        return html
      },
    },
  }, true)
}

function changeInterval(val) {
  selectedInterval.value = val
  emit('change-interval', val)
}

function handleResize() {
  chart?.resize()
}

onMounted(() => {
  renderChart()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})

watch(() => props.data, renderChart, { deep: true })
watch(chartType, renderChart)
</script>

<style lang="scss" scoped>
.stock-chart-wrapper {
  background-color: $bg-card;
  border: 1px solid $border-color;
  border-radius: $radius-lg;
  overflow: hidden;
}

.chart-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid $border-color;
  flex-wrap: wrap;
  gap: 10px;
}

.chart-toolbar strong {
  color: $text-primary;
  margin-right: 8px;
}

.chart-toolbar span {
  color: $text-muted;
  font-size: 12px;
}

.chart-body {
  min-height: 420px;
  padding: 12px;
}

.chart-container {
  width: 100%;
  height: 420px;
}
</style>
