<template>
  <div class="index-card" @click="$emit('click', index.symbol)">
    <div class="card-top">
      <span class="card-name">{{ index.name }}</span>
      <span class="card-symbol">{{ cleanSymbol(index.symbol) }}</span>
    </div>
    <div class="card-price">{{ formatPrice(index.price) }}</div>
    <div class="card-bottom">
      <span class="card-change" :class="changeClass">{{ formatChange(index.change) }}</span>
      <span class="card-pct" :class="changeClass">{{ formatPct(index.changePercent) }}</span>
    </div>
    <MiniChart :data="index.miniChart || []" />
  </div>
</template>

<script setup>
import MiniChart from '@/components/stock/MiniChart.vue'

const props = defineProps({
  index: { type: Object, required: true },
})

defineEmits(['click'])

const changeClass = computed(() => {
  const c = props.index?.change
  if (c == null) return ''
  return c >= 0 ? 'up' : 'down'
})

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

function cleanSymbol(sym) {
  return sym?.replace('^', '') || ''
}

import { computed } from 'vue'
</script>

<style lang="scss" scoped>
.index-card {
  background-color: $bg-card;
  border: 1px solid $border-color;
  border-radius: $radius-md;
  padding: 14px 16px;
  cursor: pointer;
  transition: all $transition-fast;

  &:hover {
    border-color: $color-accent;
    box-shadow: $shadow-sm;
  }
}

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.card-name {
  font-size: 13px;
  font-weight: 600;
  color: $text-primary;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-symbol {
  font-size: 11px;
  color: $text-muted;
  flex-shrink: 0;
  margin-left: 8px;
}

.card-price {
  font-size: 18px;
  font-weight: 700;
  color: $text-primary;
  font-variant-numeric: tabular-nums;
  margin-bottom: 4px;
}

.card-bottom {
  display: flex;
  gap: 8px;
  margin-bottom: 6px;
}

.card-change,
.card-pct {
  font-size: 13px;
  font-weight: 600;

  &.up { color: $color-up; }
  &.down { color: $color-down; }
}
</style>
