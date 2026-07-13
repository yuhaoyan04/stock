<template>
  <div ref="chartRef" class="mini-chart"></div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Array,
    default: () => [],
  },
  upColor: {
    type: String,
    default: '#00c853',
  },
  downColor: {
    type: String,
    default: '#ff1744',
  },
})

const chartRef = ref(null)
let chart = null

function renderChart() {
  if (!chartRef.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value)
  }

  const values = (props.data || [])
    .map(value => Number(value))
    .filter(value => Number.isFinite(value))

  if (values.length < 2) {
    chart.clear()
    return
  }

  const color = values.length > 1 && values[values.length - 1] >= values[0]
    ? props.upColor
    : props.downColor

  chart.setOption({
    grid: {
      top: 2,
      bottom: 2,
      left: 2,
      right: 2,
    },
    xAxis: {
      type: 'category',
      show: false,
      data: values.map((_, i) => i),
    },
    yAxis: {
      type: 'value',
      show: false,
      min: Math.min(...values) * 0.999,
      max: Math.max(...values) * 1.001,
    },
    series: [
      {
        type: 'line',
        data: values,
        smooth: true,
        symbol: 'none',
        lineStyle: {
          color,
          width: 1.5,
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: color + '40' },
            { offset: 1, color: color + '05' },
          ]),
        },
      },
    ],
  })
}

onMounted(() => {
  renderChart()
})

watch(() => props.data, () => {
  renderChart()
}, { deep: true })
</script>

<style lang="scss" scoped>
.mini-chart {
  width: 80px;
  height: 32px;
}
</style>
