<template>
  <div class="financial-table">
    <div class="table-toolbar">
      <div class="table-title">财务报表</div>
      <div class="table-controls">
        <el-radio-group v-model="statementType" size="small" @change="changeType">
          <el-radio-button value="income">利润表</el-radio-button>
          <el-radio-button value="balance">资产负债表</el-radio-button>
          <el-radio-button value="cashflow">现金流</el-radio-button>
        </el-radio-group>
        <el-radio-group v-model="period" size="small" @change="changePeriod">
          <el-radio-button value="annual">年报</el-radio-button>
          <el-radio-button value="quarterly">季报</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <div class="table-container" v-loading="loading">
      <template v-if="columns.length > 0 && rows.length > 0">
        <el-table
          :data="rows"
          :border="true"
          :stripe="true"
          size="small"
          max-height="400"
          style="width: 100%"
        >
          <el-table-column
            prop="label"
            label="项目"
            width="160"
            fixed="left"
          >
            <template #default="{ row }">
              <span class="row-label">{{ row.label }}</span>
            </template>
          </el-table-column>
          <el-table-column
            v-for="col in columns"
            :key="col"
            :label="formatColumnLabel(col)"
            :prop="col"
            align="right"
            min-width="110"
          >
            <template #default="{ row }">
              <span class="cell-value">{{ formatCellValue(row[col]) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </template>
      <template v-else>
        <el-empty description="暂无财务数据" :image-size="80" />
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { getFinancials } from '@/api'

const props = defineProps({
  symbol: { type: String, required: true },
})

const statementType = ref('income')
const period = ref('annual')
const rawData = ref([])
const loading = ref(false)

const columns = computed(() => {
  if (rawData.value.length === 0) return []
  const cols = rawData.value.map(r => r.date).filter(Boolean)
  return cols
})

const rows = computed(() => {
  if (rawData.value.length === 0 || columns.value.length === 0) return []

  // 收集所有唯一的指标名
  const metricSet = new Set()
  rawData.value.forEach(row => {
    Object.keys(row).forEach(k => {
      if (k !== 'date') metricSet.add(k)
    })
  })

  const result = []
  metricSet.forEach(metric => {
    const row = { label: metric }
    columns.value.forEach(dateCol => {
      const record = rawData.value.find(r => r.date === dateCol)
      row[dateCol] = record ? record[metric] : null
    })
    result.push(row)
  })

  return result
})

function formatColumnLabel(dateStr) {
  try {
    const dt = new Date(dateStr)
    return dt.getFullYear() + (period.value === 'quarterly' ? '/' + (dt.getMonth() + 1) : '')
  } catch {
    return dateStr
  }
}

function formatCellValue(val) {
  if (val == null) return '—'
  if (typeof val === 'number') {
    if (!Number.isFinite(val)) return '—'
    const absVal = Math.abs(val)
    if (absVal >= 1e12) return (val / 1e12).toFixed(2) + 'T'
    if (absVal >= 1e9) return (val / 1e9).toFixed(2) + 'B'
    if (absVal >= 1e6) return (val / 1e6).toFixed(2) + 'M'
    if (absVal >= 1e3) return (val / 1e3).toFixed(1) + 'K'
    return val.toLocaleString('en-US', { maximumFractionDigits: 2 })
  }
  return String(val)
}

async function fetchData() {
  loading.value = true
  try {
    const res = await getFinancials(props.symbol, statementType.value, period.value)
    rawData.value = res.data.data || []
  } catch (e) {
    rawData.value = []
  } finally {
    loading.value = false
  }
}

function changeType() {
  fetchData()
}

function changePeriod() {
  fetchData()
}

watch(() => props.symbol, () => {
  fetchData()
}, { immediate: true })
</script>

<style lang="scss" scoped>
.financial-table {
  background-color: $bg-card;
  border: 1px solid $border-color;
  border-radius: $radius-lg;
  overflow: hidden;
}

.table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid $border-color;
  flex-wrap: wrap;
  gap: 8px;
}

.table-title {
  font-size: 16px;
  font-weight: 600;
  color: $text-primary;
}

.table-controls {
  display: flex;
  gap: 12px;
}

.table-container {
  padding: 12px;
}

.row-label {
  font-weight: 600;
  font-size: 13px;
  color: $text-primary;
}

.cell-value {
  font-variant-numeric: tabular-nums;
  font-size: 13px;
}
</style>
