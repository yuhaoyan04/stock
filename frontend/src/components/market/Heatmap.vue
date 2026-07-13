<template>
  <div class="heatmap-panel">
    <div class="section-header">
      <h2 class="section-title">热门股票</h2>
    </div>
    <el-table
      :data="stocks"
      :stripe="true"
      size="small"
      @row-click="handleRowClick"
      style="width: 100%; cursor: pointer"
      v-loading="loading"
    >
      <el-table-column prop="symbol" label="代码" width="90">
        <template #default="{ row }">
          <span class="table-symbol">{{ row.symbol }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="名称" min-width="140">
        <template #default="{ row }">
          <div class="name-cell">
            <span>{{ row.name }}</span>
            <el-tag size="small" type="info" v-if="row.sector">{{ row.sector }}</el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="走势" width="100" align="center">
        <template #default="{ row }">
          <MiniChart :data="row.miniChart || []" />
        </template>
      </el-table-column>
      <el-table-column label="价格" width="110" align="right">
        <template #default="{ row }">
          <span class="price-cell">{{ formatPrice(row.price) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="涨跌幅" width="120" align="right">
        <template #default="{ row }">
          <div class="change-cell" :class="getChangeClass(row.change)">
            <span class="change-val">{{ formatChange(row.change) }}</span>
            <span class="change-pct">{{ formatPct(row.changePercent) }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="市值" width="120" align="right">
        <template #default="{ row }">
          <span class="text-muted">{{ formatCap(row.marketCap) }}</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import MiniChart from '@/components/stock/MiniChart.vue'

const props = defineProps({
  stocks: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

const router = useRouter()

function handleRowClick(row) {
  router.push(`/stock/${row.symbol}`)
}

function formatPrice(val) {
  if (val == null || !Number.isFinite(Number(val))) return '—'
  return Number(val).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatChange(val) {
  if (val == null || !Number.isFinite(Number(val))) return '—'
  const sign = val >= 0 ? '+' : ''
  return sign + Number(val).toFixed(2)
}

function formatPct(val) {
  if (val == null || !Number.isFinite(Number(val))) return '—'
  const sign = val >= 0 ? '+' : ''
  return sign + Number(val).toFixed(2) + '%'
}

function formatCap(val) {
  if (val == null || !Number.isFinite(Number(val))) return '—'
  if (val >= 1e12) return '$' + (val / 1e12).toFixed(1) + 'T'
  if (val >= 1e9) return '$' + (val / 1e9).toFixed(1) + 'B'
  if (val >= 1e6) return '$' + (val / 1e6).toFixed(0) + 'M'
  return '$' + val.toLocaleString()
}

function getChangeClass(val) {
  if (val == null || !Number.isFinite(Number(val))) return ''
  return Number(val) >= 0 ? 'up' : 'down'
}
</script>

<style lang="scss" scoped>
.heatmap-panel {
  background-color: $bg-card;
  border: 1px solid $border-color;
  border-radius: $radius-lg;
  overflow: hidden;
}

.section-header {
  padding: 14px 16px;
  border-bottom: 1px solid $border-color;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: $text-primary;
}

.table-symbol {
  font-weight: 700;
  color: $color-accent;
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.price-cell {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.change-cell {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  font-weight: 600;
  font-variant-numeric: tabular-nums;

  &.up { color: $color-up; }
  &.down { color: $color-down; }
}
</style>
