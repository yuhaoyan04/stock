<template>
  <div class="stock-search">
    <el-select
      v-model="selectedSymbol"
      filterable
      remote
      reserve-keyword
      placeholder="搜索股票代码或名称（如 AAPL, Tesla, 苹果）..."
      :remote-method="searchStocks"
      :loading="loading"
      clearable
      value-key="symbol"
      class="search-select"
      @change="handleSelect"
      @visible-change="handleVisibleChange"
      popper-class="search-popper"
    >
      <template #empty>
        <div class="search-empty">
          <template v-if="query.length > 0">
            <p>未找到 "{{ query }}" 相关结果</p>
            <p class="hint">尝试输入股票代码（如 AAPL）或公司名称（如 Apple）</p>
          </template>
          <template v-else>
            <p>热门资产与中文名称已支持搜索</p>
            <p class="hint">点击任意候选即可进入详情；输入“苹果 / 英伟达 / 标普500”试试</p>
          </template>
        </div>
      </template>
      <el-option
        v-for="item in results"
        :key="item.symbol"
        :label="item.symbol"
        :value="item"
      >
        <div class="search-option">
          <div class="option-left">
            <span class="option-symbol">{{ item.symbol }}</span>
            <el-tag
              :type="getTagType(item.type)"
              size="small"
              class="option-type"
            >
              {{ getTypeLabel(item.type) }}
            </el-tag>
          </div>
          <div class="option-right">
            <span class="option-name">{{ item.name }}</span>
            <span v-if="item.aliases?.length" class="option-alias">{{ item.aliases.slice(0, 2).join(' · ') }}</span>
            <span class="option-exchange" v-if="item.exchange">{{ item.exchange }}</span>
          </div>
        </div>
      </el-option>
    </el-select>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { searchSymbols } from '@/api'

const emit = defineEmits(['select'])
const selectedSymbol = ref(null)
const results = ref([])
const loading = ref(false)
const query = ref('')

let searchTimer = null

function searchStocks(q) {
  query.value = q || ''
  if (!q || q.trim().length < 1) {
    loadFeatured()
    return
  }
  loading.value = true
  clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    try {
      const res = await searchSymbols(q, 15)
      results.value = res.data.results
    } catch (e) {
      results.value = []
    } finally {
      loading.value = false
    }
  }, 300)
}

async function loadFeatured() {
  if (results.value.length) return
  loading.value = true
  try {
    const res = await searchSymbols('', 12)
    results.value = res.data.results || []
  } catch {
    results.value = []
  } finally {
    loading.value = false
  }
}

function handleVisibleChange(visible) {
  if (visible && !query.value) loadFeatured()
}

function handleSelect(item) {
  if (item && item.symbol) {
    emit('select', item.symbol)
    selectedSymbol.value = null
  }
}

function getTypeLabel(type) {
  const map = {
    stock: '股票',
    etf: 'ETF',
    index: '指数',
    future: '期货',
    forex: '外汇',
    crypto: '加密',
  }
  return map[type] || type || '未知'
}

function getTagType(type) {
  const map = {
    stock: 'primary',
    etf: 'success',
    index: 'warning',
    future: 'danger',
    forex: 'info',
    crypto: '',
  }
  return map[type] || 'info'
}
</script>

<style lang="scss" scoped>
.stock-search {
  width: 100%;
}

.search-select {
  width: 100%;
}

.search-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 12px;
}

.option-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 120px;
}

.option-symbol {
  font-weight: 700;
  font-size: 14px;
  color: $text-primary;
}

.option-type {
  flex-shrink: 0;
}

.option-right {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  overflow: hidden;
}

.option-name {
  font-size: 13px;
  color: $text-secondary;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.option-alias {
  color: $color-accent-light;
  font-size: 11px;
  margin-top: 2px;
}

.option-exchange {
  font-size: 11px;
  color: $text-muted;
}

.search-empty {
  padding: 20px;
  text-align: center;
  color: $text-muted;

  .hint {
    font-size: 12px;
    margin-top: 8px;
  }
}
</style>
