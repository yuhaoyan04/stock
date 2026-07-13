import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/api'
import { getApiErrorMessage } from '@/api'

export const useStockStore = defineStore('stock', () => {
  const marketData = ref(null)
  const marketMeta = ref({})
  const marketError = ref('')
  const marketLoading = ref(false)
  const searchResults = ref([])
  const searchLoading = ref(false)
  const currentStock = ref(null)
  const stockMeta = ref({})
  const stockError = ref('')
  const stockLoading = ref(false)
  const historyData = ref([])
  const historyMeta = ref({})
  const historyError = ref('')
  const historyLoading = ref(false)
  const financialsData = ref([])
  const financialsMeta = ref({})
  const financialsError = ref('')
  const financialsLoading = ref(false)
  const categories = ref(null)

  const stockPrice = computed(() => currentStock.value?.currentPrice ?? null)
  const stockChange = computed(() => {
    if (currentStock.value?.currentPrice == null || currentStock.value?.previousClose == null) return null
    return currentStock.value.currentPrice - currentStock.value.previousClose
  })
  const stockChangePercent = computed(() => {
    if (stockChange.value == null || currentStock.value?.previousClose == null || Number(currentStock.value.previousClose) === 0) return null
    return (stockChange.value / currentStock.value.previousClose) * 100
  })

  async function fetchMarketOverview() {
    marketLoading.value = true
    marketError.value = ''
    try {
      const res = await api.getMarketOverview()
      marketData.value = res.data
      marketMeta.value = res.meta || {}
    } catch (e) {
      marketError.value = getApiErrorMessage(e, '市场概览加载失败')
      marketData.value = null
    } finally {
      marketLoading.value = false
    }
  }

  async function fetchSearchResults(query) {
    searchLoading.value = true
    try {
      const res = await api.searchSymbols(query)
      searchResults.value = res.data.results || []
    } catch (e) {
      searchResults.value = []
    } finally {
      searchLoading.value = false
    }
  }

  async function fetchStockInfo(symbol) {
    stockLoading.value = true
    stockError.value = ''
    try {
      const res = await api.getStockInfo(symbol)
      currentStock.value = res.data
      stockMeta.value = res.meta || {}
      return res.data
    } catch (e) {
      stockError.value = getApiErrorMessage(e, '资产信息加载失败')
      currentStock.value = null
      stockMeta.value = {}
      return null
    } finally {
      stockLoading.value = false
    }
  }

  async function fetchStockHistory(symbol, period = '1mo', interval = '1d') {
    historyLoading.value = true
    historyError.value = ''
    try {
      const res = await api.getStockHistory(symbol, period, interval)
      historyData.value = res.data.data || []
      historyMeta.value = res.meta || {}
      return historyData.value
    } catch (e) {
      historyError.value = getApiErrorMessage(e, '历史行情加载失败')
      historyData.value = []
      historyMeta.value = {}
      return []
    } finally {
      historyLoading.value = false
    }
  }

  async function fetchFinancials(symbol, type = 'income', period = 'annual') {
    financialsLoading.value = true
    financialsError.value = ''
    try {
      const res = await api.getFinancials(symbol, type, period)
      financialsData.value = res.data.data || []
      financialsMeta.value = res.meta || {}
      return financialsData.value
    } catch (e) {
      financialsError.value = getApiErrorMessage(e, '财务数据加载失败')
      financialsData.value = []
      financialsMeta.value = {}
      return []
    } finally {
      financialsLoading.value = false
    }
  }

  async function fetchCategories() {
    try {
      const res = await api.getCategories()
      categories.value = res.data
    } catch (e) {
      categories.value = null
    }
  }

  return {
    marketData,
    marketMeta,
    marketError,
    marketLoading,
    searchResults,
    searchLoading,
    currentStock,
    stockMeta,
    stockError,
    stockLoading,
    historyData,
    historyMeta,
    historyError,
    historyLoading,
    financialsData,
    financialsMeta,
    financialsError,
    financialsLoading,
    categories,
    stockPrice,
    stockChange,
    stockChangePercent,
    fetchMarketOverview,
    fetchSearchResults,
    fetchStockInfo,
    fetchStockHistory,
    fetchFinancials,
    fetchCategories,
  }
})
