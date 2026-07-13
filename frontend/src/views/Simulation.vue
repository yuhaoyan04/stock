<template>
  <div class="simulation-page">
    <div class="page-header">
      <div>
        <h1>虚拟账户</h1>
        <p>模拟美股交易 — 支持市价/限价/止损/止损限价单，使用 yfinance 实时行情。</p>
      </div>
      <div class="header-actions">
        <el-tag v-if="marketStatus" :type="marketStatus.isOpen ? 'success' : 'info'" size="small" class="market-tag">
          {{ marketStatus.label }}
        </el-tag>
        <el-button :loading="loading" @click="refreshAll">刷新账户</el-button>
      </div>
    </div>
    <ModuleGuide title="虚拟账户" description="这是一个由后端统一计算现金、持仓和盈亏的练习账户，不连接真实券商。" :steps="['确认账户现金和现有持仓。', '输入 ticker、方向、数量和订单类型；市价单可由后端获取最新价。', '提交后在持仓和交易记录中核对成交、成本和盈亏。']" note="不允许融资或卖空；行情延迟、限价和止损条件都会影响是否成交。" class="mb-4" />

    <DataQualityBar v-if="meta" class="mb-4" :meta="meta" />

    <StateBlock v-if="errorMessage" type="error" title="账户加载失败" :description="errorMessage" class="mb-4">
      <template #action>
        <el-button size="small" @click="refreshAll">重试</el-button>
      </template>
    </StateBlock>

    <!-- 账户概览卡片 -->
    <div class="overview-grid" v-loading="loading">
      <div v-for="card in overviewCards" :key="card.label" class="overview-card">
        <span>{{ card.label }}</span>
        <strong :class="card.className">{{ card.value }}</strong>
      </div>
    </div>

    <section class="panel template-panel mt-4">
      <div class="panel-title">
        <div>
          <h2>组合模板</h2>
          <span>用一组清晰的 ETF 配置开始模拟，不需要逐只下单</span>
        </div>
        <el-tag size="small" type="warning">纸面交易</el-tag>
      </div>
      <div v-if="templateLoading" class="template-loading">正在读取组合模板...</div>
      <div v-else class="template-grid">
        <article v-for="template in templates" :key="template.id" class="template-card" :class="{ selected: selectedTemplateId === template.id }" @click="selectedTemplateId = template.id">
          <div class="template-card-head">
            <div>
              <strong>{{ template.name }}</strong>
              <span>{{ template.style }}</span>
            </div>
            <el-radio v-model="selectedTemplateId" :label="template.id">选择</el-radio>
          </div>
          <p>{{ template.description }}</p>
          <div class="template-holdings">
            <el-tag v-for="holding in template.holdings" :key="holding.symbol" size="small">{{ holding.symbol }} {{ formatPercent(holding.weight, { signed: false }) }}</el-tag>
          </div>
        </article>
      </div>
      <div v-if="selectedTemplate" class="template-action-row">
        <span>本次投入金额</span>
        <el-input-number v-model="templateCapital" :min="1" :max="Number(account.cash || 1)" :precision="2" controls-position="right" />
        <el-button type="primary" :loading="templateSubmitting" :disabled="!account.cash" @click="buyTemplate">按此组合买入</el-button>
        <small>将按比例买入零股，最终以后台现金和成交校验为准。</small>
      </div>
    </section>

    <!-- PnL 走势迷你图 -->
    <section v-if="sparklineData.length >= 2" class="panel sparkline-panel">
      <div class="panel-title">
        <h2>累计盈亏走势</h2>
        <span>近 {{ sparklineData.length }} 天</span>
      </div>
      <div ref="sparklineRef" class="sparkline-chart"></div>
    </section>

    <!-- 下单面板 + 持仓表格 -->
    <div class="workspace-grid mt-4">
      <section class="panel order-panel">
        <div class="panel-title">
          <h2>下单面板</h2>
          <span v-if="marketStatus && !marketStatus.isOpen" class="market-hint">当前{{ marketStatus.label }}，订单可能无法立即成交</span>
        </div>

        <el-form label-position="top" @submit.prevent>
          <el-form-item label="订单类型">
            <el-segmented v-model="order.orderType" :options="orderTypeOptions" />
          </el-form-item>
          <el-form-item label="方向">
            <el-segmented v-model="order.side" :options="sideOptions" />
          </el-form-item>
          <el-form-item label="Ticker">
            <el-input v-model="order.symbol" placeholder="例如 AAPL" @input="order.symbol = order.symbol.toUpperCase()" />
          </el-form-item>
          <el-form-item label="数量">
            <el-input-number v-model="order.quantity" :min="1" :precision="4" :step="1" controls-position="right" class="full-input" />
          </el-form-item>

          <!-- 限价单：显示限价输入 -->
          <el-form-item v-if="order.orderType === 'limit' || order.orderType === 'stop_limit'" label="限价 ($)">
            <el-input-number v-model="order.limitPrice" :min="0.01" :precision="2" :step="0.01" controls-position="right" class="full-input" />
          </el-form-item>

          <!-- 止损单：显示触发价输入 -->
          <el-form-item v-if="order.orderType === 'stop' || order.orderType === 'stop_limit'" label="触发价 ($)">
            <el-input-number v-model="order.stopPrice" :min="0.01" :precision="2" :step="0.01" controls-position="right" class="full-input" />
          </el-form-item>

          <!-- 市价单：可选限价 -->
          <el-form-item v-if="order.orderType === 'market'" label="成交价（可选）">
            <el-input-number v-model="order.price" :min="0" :precision="4" :step="1" controls-position="right" class="full-input" />
            <p class="form-hint">留空时后端自动获取 yfinance 最新价</p>
          </el-form-item>

          <el-form-item label="手续费（可选）">
            <el-input-number v-model="order.fee" :min="0" :precision="2" :step="0.01" controls-position="right" class="full-input" />
            <p class="form-hint">留空自动计算（交易金额 × 0.00278%，最低 $0.01）</p>
          </el-form-item>
          <div class="estimate-row">
            <span>{{ estimatedLabel }}</span>
            <strong>{{ estimatedAmount }}</strong>
          </div>
          <el-button type="primary" :loading="submitting" class="submit-btn" @click="submitOrder">
            {{ submitBtnLabel }}
          </el-button>
        </el-form>
      </section>

      <section class="panel positions-panel">
        <div class="panel-title">
          <h2>持仓</h2>
          <span>{{ positions.length }} 个标的</span>
        </div>
        <el-table :data="positions" size="small" border empty-text="暂无持仓">
          <el-table-column prop="symbol" label="Ticker" width="90">
            <template #default="{ row }">
              <span class="symbol-cell">{{ row.symbol }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="名称" min-width="150" show-overflow-tooltip />
          <el-table-column label="数量" width="100" align="right">
            <template #default="{ row }">{{ formatNumber(row.quantity, 4) }}</template>
          </el-table-column>
          <el-table-column label="成本价" width="110" align="right">
            <template #default="{ row }">{{ formatPrice(row.averageCost) }}</template>
          </el-table-column>
          <el-table-column label="最新价" width="110" align="right">
            <template #default="{ row }">{{ formatPrice(row.latestPrice) }}</template>
          </el-table-column>
          <el-table-column label="市值" width="120" align="right">
            <template #default="{ row }">{{ formatCompact(row.marketValue, { currency: '$' }) }}</template>
          </el-table-column>
          <el-table-column label="未实现盈亏" width="140" align="right">
            <template #default="{ row }">
              <span :class="valueClass(row.unrealizedPnl)">{{ formatCompact(row.unrealizedPnl, { currency: '$' }) }} / {{ formatPercent(row.unrealizedPnlPercent) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </div>

    <!-- 挂单表格 -->
    <section class="panel pending-panel mt-4">
      <div class="panel-title">
        <h2>挂单</h2>
        <span>{{ pendingOrders.length }} 个待成交</span>
      </div>
      <el-table :data="pendingOrders" size="small" border empty-text="暂无挂单">
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ orderTypeLabel(row.order_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="方向" width="70">
          <template #default="{ row }">
            <el-tag :type="row.side === 'buy' ? 'success' : 'danger'" size="small">{{ row.side === 'buy' ? '买' : '卖' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="symbol" label="Ticker" width="90" />
        <el-table-column label="数量" width="100" align="right">
          <template #default="{ row }">{{ formatNumber(row.quantity, 4) }}</template>
        </el-table-column>
        <el-table-column label="限价" width="110" align="right">
          <template #default="{ row }">{{ row.limit_price ? formatPrice(row.limit_price) : '-' }}</template>
        </el-table-column>
        <el-table-column label="触发价" width="110" align="right">
          <template #default="{ row }">{{ row.stop_price ? formatPrice(row.stop_price) : '-' }}</template>
        </el-table-column>
        <el-table-column label="手续费" width="100" align="right">
          <template #default="{ row }">{{ formatPrice(row.fee) }}</template>
        </el-table-column>
        <el-table-column label="时间" min-width="150">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="danger" text @click="cancelOrder(row.id)">撤单</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <!-- 交易记录 -->
    <section class="panel trades-panel mt-4">
      <div class="panel-title">
        <h2>交易记录</h2>
        <el-button size="small" plain :disabled="submitting" @click="confirmReset">重置账户</el-button>
      </div>
      <el-table :data="trades" size="small" border empty-text="暂无交易记录">
        <el-table-column label="时间" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="方向" width="80">
          <template #default="{ row }">
            <el-tag :type="row.side === 'buy' ? 'success' : 'danger'" size="small">{{ row.side === 'buy' ? '买入' : '卖出' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="symbol" label="Ticker" width="90" />
        <el-table-column label="数量" width="100" align="right">
          <template #default="{ row }">{{ formatNumber(row.quantity, 4) }}</template>
        </el-table-column>
        <el-table-column label="价格" width="110" align="right">
          <template #default="{ row }">{{ formatPrice(row.price) }}</template>
        </el-table-column>
        <el-table-column label="金额" width="120" align="right">
          <template #default="{ row }">{{ formatCompact(row.gross_amount, { currency: '$' }) }}</template>
        </el-table-column>
        <el-table-column label="手续费" width="100" align="right">
          <template #default="{ row }">{{ formatPrice(row.fee) }}</template>
        </el-table-column>
        <el-table-column label="已实现盈亏" width="130" align="right">
          <template #default="{ row }">
            <span :class="valueClass(row.realized_pnl)">{{ formatCompact(row.realized_pnl, { currency: '$' }) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import {
  cancelSimulationOrder,
  getApiErrorMessage,
  getSimulationAccount,
  getSimulationMarketStatus,
  getSimulationPendingOrders,
  getSimulationTemplates,
  buySimulationTemplate,
  resetSimulationAccount,
  submitSimulationOrder,
} from '@/api'
import DataQualityBar from '@/components/common/DataQualityBar.vue'
import ModuleGuide from '@/components/common/ModuleGuide.vue'
import StateBlock from '@/components/common/StateBlock.vue'
import { formatCompact, formatDateTime, formatNumber, formatPercent, formatPrice, valueClass } from '@/utils/formatters'

const loading = ref(false)
const submitting = ref(false)
const errorMessage = ref('')
const snapshot = ref({ account: {}, positions: [], trades: [] })
const meta = ref({})
const marketStatus = ref(null)
const pendingOrders = ref([])
const sparklineChart = ref(null)
const sparklineRef = ref(null)
const templates = ref([])
const selectedTemplateId = ref('')
const templateCapital = ref(null)
const templateLoading = ref(false)
const templateSubmitting = ref(false)

// ── Order state ──────────────────────────────────
const order = reactive({
  side: 'buy',
  symbol: 'AAPL',
  quantity: 1,
  orderType: 'market',
  price: null,
  limitPrice: null,
  stopPrice: null,
  fee: null,
})

const sideOptions = [
  { label: '买入', value: 'buy' },
  { label: '卖出', value: 'sell' },
]

const orderTypeOptions = [
  { label: '市价', value: 'market' },
  { label: '限价', value: 'limit' },
  { label: '止损', value: 'stop' },
  { label: '止损限价', value: 'stop_limit' },
]

const orderTypeMap = { market: '市价', limit: '限价', stop: '止损', stop_limit: '止损限价' }

function orderTypeLabel(type) {
  return orderTypeMap[type] || type || '-'
}

// ── Computed ─────────────────────────────────────
const account = computed(() => snapshot.value.account || {})
const positions = computed(() => snapshot.value.positions || [])
const trades = computed(() => snapshot.value.trades || [])
const sparklineData = computed(() => account.value.sparkline || [])
const selectedTemplate = computed(() => templates.value.find(item => item.id === selectedTemplateId.value))

const overviewCards = computed(() => [
  { label: '总资产', value: formatCompact(account.value.totalAssets, { currency: '$' }), className: '' },
  { label: '现金', value: formatCompact(account.value.cash, { currency: '$' }), className: '' },
  { label: '持仓市值', value: formatCompact(account.value.holdingsValue, { currency: '$' }), className: '' },
  { label: '今日盈亏', value: account.value.todayPnl != null ? formatCompact(account.value.todayPnl, { currency: '$' }) : '-', className: valueClass(account.value.todayPnl) },
  { label: '累计盈亏', value: `${formatCompact(account.value.cumulativePnl, { currency: '$' })} / ${formatPercent(account.value.cumulativePnlPercent)}`, className: valueClass(account.value.cumulativePnl) },
  { label: '已实现盈亏', value: formatCompact(account.value.realizedPnl, { currency: '$' }), className: valueClass(account.value.realizedPnl) },
])

const submitBtnLabel = computed(() => {
  const sideLabel = order.side === 'buy' ? '买入' : '卖出'
  const typeLabel = orderTypeMap[order.orderType] || ''
  return order.orderType === 'market' ? `确认${sideLabel}` : `提交${typeLabel}${sideLabel}单`
})

const estimatedLabel = computed(() => {
  if (order.orderType !== 'market') return '预计触发时金额（估算）'
  if (!Number.isFinite(Number(order.price))) return '以实时价估算'
  return '估算金额'
})

const estimatedAmount = computed(() => {
  const qty = Number(order.quantity) || 0
  const usePrice = order.orderType === 'market' && Number.isFinite(Number(order.price))
    ? Number(order.price)
    : (Number.isFinite(Number(order.limitPrice)) ? Number(order.limitPrice) : 0)
  if (!qty || !usePrice) return order.orderType === 'market' ? '使用实时价估算' : '请输入价格'
  const gross = usePrice * qty
  const feeVal = Number.isFinite(Number(order.fee)) ? Number(order.fee) : (gross * 0.0000278)
  const total = order.side === 'buy' ? gross + feeVal : gross - feeVal
  return formatCompact(total, { currency: '$' })
})

// ── Methods ──────────────────────────────────────
async function refreshAll() {
  await Promise.all([loadAccount(), loadPendingOrders(), loadMarketStatus()])
}

async function loadTemplates() {
  templateLoading.value = true
  try {
    const res = await getSimulationTemplates()
    templates.value = res.data.templates || []
    selectedTemplateId.value = selectedTemplateId.value || templates.value[0]?.id || ''
  } catch {
    templates.value = []
  } finally {
    templateLoading.value = false
  }
}

async function buyTemplate() {
  if (!selectedTemplate.value) return
  try {
    await ElMessageBox.confirm(`确认按“${selectedTemplate.value.name}”买入模拟组合？这会使用纸面账户资金。`, '确认模拟买入', { type: 'warning' })
  } catch {
    return
  }
  templateSubmitting.value = true
  try {
    const res = await buySimulationTemplate({
      template_id: selectedTemplate.value.id,
      capital: templateCapital.value == null ? Number(account.value.cash) : Number(templateCapital.value),
    })
    snapshot.value = res.data
    meta.value = res.meta || {}
    await nextTick()
    renderSparkline()
    ElMessage.success('模拟组合已买入')
  } catch (e) {
    ElMessage.error(getApiErrorMessage(e, '组合模板买入失败'))
  } finally {
    templateSubmitting.value = false
  }
}

async function loadAccount() {
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await getSimulationAccount()
    snapshot.value = res.data
    meta.value = res.meta || {}
    await nextTick()
    renderSparkline()
  } catch (e) {
    errorMessage.value = getApiErrorMessage(e, '虚拟账户加载失败')
  } finally {
    loading.value = false
  }
}

async function loadPendingOrders() {
  try {
    const res = await getSimulationPendingOrders()
    pendingOrders.value = res.data.orders || []
  } catch {
    pendingOrders.value = []
  }
}

async function loadMarketStatus() {
  try {
    const res = await getSimulationMarketStatus()
    marketStatus.value = res.data
  } catch {
    marketStatus.value = null
  }
}

function validateOrder() {
  if (!order.symbol.trim()) return 'Ticker 不能为空'
  if (!Number.isFinite(Number(order.quantity)) || Number(order.quantity) <= 0) return '数量必须大于 0'
  if (order.orderType === 'limit' || order.orderType === 'stop_limit') {
    if (!Number.isFinite(Number(order.limitPrice)) || Number(order.limitPrice) <= 0) return '请设置有效限价'
  }
  if (order.orderType === 'stop' || order.orderType === 'stop_limit') {
    if (!Number.isFinite(Number(order.stopPrice)) || Number(order.stopPrice) <= 0) return '请设置有效触发价'
  }
  if (Number.isFinite(Number(order.fee)) && Number(order.fee) < 0) return '手续费不能为负'
  return ''
}

async function submitOrder() {
  const validation = validateOrder()
  if (validation) {
    ElMessage.warning(validation)
    return
  }
  submitting.value = true
  try {
    const payload = {
      side: order.side,
      symbol: order.symbol.trim().toUpperCase(),
      quantity: Number(order.quantity),
      order_type: order.orderType,
    }
    if (order.orderType === 'market') {
      if (order.price != null && order.price !== '' && Number.isFinite(Number(order.price))) {
        payload.price = Number(order.price)
      }
    }
    if (order.orderType === 'limit' || order.orderType === 'stop_limit') {
      payload.limit_price = Number(order.limitPrice)
    }
    if (order.orderType === 'stop' || order.orderType === 'stop_limit') {
      payload.stop_price = Number(order.stopPrice)
    }
    if (order.fee != null && order.fee !== '' && Number.isFinite(Number(order.fee))) {
      payload.fee = Number(order.fee)
    }
    const res = await submitSimulationOrder(payload)
    snapshot.value = res.data
    meta.value = res.meta || {}
    await loadPendingOrders()
    await nextTick()
    renderSparkline()
    const msg = order.orderType === 'market' ? '订单已成交' : '订单已提交，等待条件满足后成交'
    ElMessage.success(msg)
  } catch (e) {
    ElMessage.error(getApiErrorMessage(e, '下单失败'))
  } finally {
    submitting.value = false
  }
}

async function cancelOrder(orderId) {
  try {
    await cancelSimulationOrder(orderId)
    ElMessage.success('订单已撤销')
    await loadPendingOrders()
  } catch (e) {
    ElMessage.error(getApiErrorMessage(e, '撤单失败'))
  }
}

async function confirmReset() {
  try {
    await ElMessageBox.confirm('确认重置虚拟账户？这会清空持仓、挂单和交易记录。', '重置账户', { type: 'warning' })
    const res = await resetSimulationAccount()
    snapshot.value = res.data
    meta.value = res.meta || {}
    pendingOrders.value = []
    await nextTick()
    renderSparkline()
    ElMessage.success('账户已重置')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(getApiErrorMessage(e, '重置失败'))
  }
}

// ── Sparkline ────────────────────────────────────
function renderSparkline() {
  const chartDom = sparklineRef.value
  if (!chartDom) return
  const data = sparklineData.value
  if (!data || data.length < 2) {
    if (sparklineChart.value) sparklineChart.value.clear()
    return
  }
  if (!sparklineChart.value) {
    sparklineChart.value = echarts.init(chartDom, 'dark')
  }
  const values = data.map(d => d.cumulativePnl)
  const positive = values[values.length - 1] >= values[0]
  const color = positive ? '#00c853' : '#ff1744'
  sparklineChart.value.setOption({
    grid: { top: 6, bottom: 6, left: 6, right: 6 },
    xAxis: { type: 'category', show: false, data: data.map(d => d.date) },
    yAxis: { type: 'value', show: false, splitLine: { show: false } },
    series: [{
      type: 'line',
      data: values,
      smooth: true,
      symbol: 'none',
      lineStyle: { color, width: 2 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: color + '40' },
          { offset: 1, color: color + '05' },
        ]),
      },
    }],
  }, true)
}

function handleResize() {
  sparklineChart.value?.resize()
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  refreshAll()
  loadTemplates()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  sparklineChart.value?.dispose()
})
</script>

<style lang="scss" scoped>
.simulation-page { max-width: 1440px; margin: 0 auto; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 18px; }
.page-header h1 { color: $text-primary; font-size: 22px; margin-bottom: 4px; }
.page-header p { color: $text-secondary; font-size: 14px; }
.header-actions { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.market-tag { font-weight: 600; }
.market-hint { color: $color-warning !important; font-weight: 500; }

.overview-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; min-height: 96px; }
.overview-card, .panel { background: $bg-card; border: 1px solid $border-color; border-radius: $radius-lg; }
.overview-card { padding: 14px 16px; display: flex; flex-direction: column; justify-content: space-between; min-height: 88px; }
.overview-card span { color: $text-muted; font-size: 12px; }
.overview-card strong { color: $text-primary; font-size: 21px; font-variant-numeric: tabular-nums; }

.sparkline-panel { margin-top: 16px; padding: 16px; }
.template-panel { margin-top: 16px; padding: 16px; }
.template-loading { color: $text-muted; font-size: 13px; padding: 12px 0; }
.template-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.template-card { min-height: 170px; border: 1px solid $border-color; border-radius: $radius-md; padding: 12px; background: $bg-secondary; cursor: pointer; transition: border-color $transition-fast, background $transition-fast; }
.template-card:hover, .template-card.selected { border-color: $color-accent; background: rgba(79, 140, 255, 0.08); }
.template-card-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; }
.template-card-head strong { display: block; color: $text-primary; font-size: 14px; }
.template-card-head span { display: block; color: $color-accent-light; font-size: 11px; margin-top: 4px; }
.template-card p { min-height: 38px; color: $text-secondary; font-size: 12px; line-height: 1.5; margin: 12px 0; }
.template-holdings { display: flex; flex-wrap: wrap; gap: 5px; }
.template-action-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-top: 14px; padding-top: 14px; border-top: 1px solid $border-color; color: $text-secondary; font-size: 13px; }
.template-action-row small { color: $text-muted; }
.sparkline-chart { width: 100%; height: 80px; }

.workspace-grid { display: grid; grid-template-columns: minmax(360px, 0.45fr) minmax(640px, 1fr); gap: 16px; }
.panel { padding: 16px; }
.panel-title { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
.panel-title h2 { color: $text-primary; font-size: 16px; font-weight: 700; }
.panel-title span { color: $text-muted; font-size: 12px; }

.full-input { width: 100%; }
.form-hint { color: $text-muted; font-size: 12px; margin-top: 6px; line-height: 1.4; }
.estimate-row { display: flex; align-items: center; justify-content: space-between; border: 1px solid $border-color; background: $bg-secondary; border-radius: $radius-md; padding: 10px 12px; margin-bottom: 12px; color: $text-secondary; }
.estimate-row strong { color: $text-primary; }
.submit-btn { width: 100%; }
.symbol-cell { color: $color-accent; font-weight: 700; }
.pending-panel, .trades-panel { margin-top: 18px; }

@media (max-width: 1200px) { .template-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 1100px) { .workspace-grid { grid-template-columns: 1fr; } }
@media (max-width: 620px) { .template-grid { grid-template-columns: 1fr; } }
</style>
