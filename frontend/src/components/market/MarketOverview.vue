<template>
  <div class="market-overview">
    <div class="section-header">
      <h2 class="section-title">核心市场资产</h2>
      <span>SPY / QQQ / VIX / 10Y / DXY / Gold / Oil / BTC</span>
    </div>
    <div v-if="indices.length || loading" class="indices-grid" v-loading="loading">
      <IndexCard v-for="idx in indices" :key="idx.symbol" :index="idx" @click="goToStock(idx.symbol)" />
    </div>
    <StateBlock v-else type="empty" title="暂无市场概览数据" description="当前数据源没有返回核心资产行情。" />
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import IndexCard from '@/components/market/IndexCard.vue'
import StateBlock from '@/components/common/StateBlock.vue'

defineProps({
  indices: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

const router = useRouter()

function goToStock(symbol) {
  router.push(`/stock/${encodeURIComponent(symbol)}`)
}
</script>

<style lang="scss" scoped>
.market-overview { margin-bottom: 24px; }
.section-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.section-title { font-size: 18px; font-weight: 700; color: $text-primary; }
.section-header span { color: $text-muted; font-size: 12px; }
.indices-grid { min-height: 120px; display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }
</style>
