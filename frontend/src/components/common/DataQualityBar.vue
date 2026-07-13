<template>
  <div class="data-quality">
    <div class="quality-items">
      <span><b>数据源</b>{{ meta.source || source }}</span>
      <span><b>更新时间</b>{{ formatDateTime(meta.last_updated || updatedAt) }}</span>
      <span v-if="currency"><b>币种</b>{{ currency }}</span>
      <span v-if="exchange"><b>交易所</b>{{ exchange }}</span>
      <span><b>复权</b>{{ meta.adjusted === false ? '未声明' : '已复权/调整收盘' }}</span>
      <span><b>延迟</b>{{ meta.delayed === false ? '未声明' : '免费源可能延迟' }}</span>
      <span v-if="meta.timezone"><b>时区</b>{{ meta.timezone }}</span>
    </div>
    <div v-if="warnings.length" class="quality-warnings">
      <el-tag v-for="warning in warnings" :key="warning" type="warning" size="small">
        {{ warning }}
      </el-tag>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatDateTime } from '@/utils/formatters'

const props = defineProps({
  meta: { type: Object, default: () => ({}) },
  source: { type: String, default: 'yfinance' },
  updatedAt: { type: String, default: '' },
  currency: { type: String, default: '' },
  exchange: { type: String, default: '' },
})

const warnings = computed(() => (props.meta?.warnings || []).filter(Boolean))
</script>

<style lang="scss" scoped>
.data-quality {
  border: 1px solid $border-color;
  border-radius: $radius-md;
  background: $bg-secondary;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quality-items {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 16px;
  color: $text-secondary;
  font-size: 12px;
}

.quality-items b {
  color: $text-muted;
  font-weight: 500;
  margin-right: 5px;
}

.quality-warnings {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
</style>
