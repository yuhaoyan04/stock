<template>
  <div class="dashboard">
    <section class="page-head">
      <div>
        <p class="eyebrow">Market Dashboard</p>
        <h1>市场驾驶舱</h1>
        <p>跟踪核心指数、宏观资产和热门股票，快速进入资产详情与组合分析。</p>
      </div>
      <el-button type="primary" @click="$router.push('/portfolio')">打开组合实验室</el-button>
    </section>
    <ModuleGuide title="市场驾驶舱" description="这里用于快速建立当天的市场观察清单。先看指数与宏观资产，再从搜索或资产池进入单个标的。" :steps="['查看数据源和更新时间，确认行情可用性。', '点击指数、热门资产或顶部搜索结果进入详情。', '需要比较或回测时，将 ticker 带到对应模块。']" note="免费行情可能延迟或缺失，请以页面数据质量提示为准。" class="mb-4" />

    <DataQualityBar
      class="mb-4"
      :meta="marketMeta"
      :updated-at="marketData?.fetchedAt"
    />

    <StateBlock
      v-if="marketError"
      type="error"
      title="市场数据加载失败"
      :description="marketError"
      class="mb-4"
    >
      <template #action>
        <el-button size="small" @click="store.fetchMarketOverview()">重试</el-button>
      </template>
    </StateBlock>

    <MarketOverview
      :indices="marketData?.indices || []"
      :loading="marketLoading"
    />

    <div class="dashboard-grid">
      <section class="panel watch-panel">
        <div class="panel-title">
          <h2>自选列表</h2>
          <el-tag size="small" type="info">本地占位</el-tag>
        </div>
        <StateBlock
          type="empty"
          title="还没有自选资产"
          description="可先从 SPY、QQQ、NVDA、AAPL 等资产详情页加入关注。"
          compact
        />
        <div class="quick-list">
          <button v-for="item in quickAssets" :key="item.symbol" @click="goToStock(item.symbol)">
            <strong>{{ item.symbol }}</strong>
            <span>{{ item.name }}</span>
          </button>
        </div>
      </section>

      <section class="panel recent-panel">
        <div class="panel-title">
          <h2>最近查看</h2>
          <el-tag size="small" type="info">预留</el-tag>
        </div>
        <StateBlock
          type="empty"
          title="暂无最近查看记录"
          description="打开资产详情后，可在下一轮迭代接入本地历史记录。"
          compact
        />
      </section>
    </div>

    <section class="hot-section">
      <div class="section-row">
        <h2 class="section-heading">热门资产行情</h2>
        <span>点击任意行进入资产详情</span>
      </div>
      <Heatmap
        v-if="marketData?.hotStocks?.length || marketLoading"
        :stocks="marketData?.hotStocks || []"
        :loading="marketLoading"
      />
      <StateBlock
        v-else
        type="empty"
        title="暂无热门资产数据"
        description="免费数据源暂时未返回热门股票行情。"
      />
    </section>

    <section class="category-section" v-if="categories">
      <div class="section-row">
        <h2 class="section-heading">资产池浏览</h2>
        <span>免费数据源，仅供研究和演示</span>
      </div>
      <el-tabs type="border-card" v-model="activeCategory">
        <el-tab-pane label="ETF" name="etfs">
          <div class="symbol-grid">
            <button v-for="etf in categories?.etfs || []" :key="etf.symbol" class="symbol-chip" @click="goToStock(etf.symbol)">
              <span class="chip-symbol">{{ etf.symbol }}</span>
              <span class="chip-name">{{ etf.name }}</span>
            </button>
          </div>
        </el-tab-pane>
        <el-tab-pane label="期货" name="futures">
          <div class="symbol-grid">
            <button v-for="f in categories?.futures || []" :key="f.symbol" class="symbol-chip" @click="goToStock(f.symbol)">
              <span class="chip-symbol">{{ f.symbol }}</span>
              <span class="chip-name">{{ f.name }}</span>
            </button>
          </div>
        </el-tab-pane>
        <el-tab-pane label="外汇" name="forex">
          <div class="symbol-grid">
            <button v-for="fx in categories?.forex || []" :key="fx.symbol" class="symbol-chip" @click="goToStock(fx.symbol)">
              <span class="chip-symbol">{{ fx.symbol }}</span>
              <span class="chip-name">{{ fx.name }}</span>
            </button>
          </div>
        </el-tab-pane>
        <el-tab-pane label="加密货币" name="crypto">
          <div class="symbol-grid">
            <button v-for="c in categories?.crypto || []" :key="c.symbol" class="symbol-chip" @click="goToStock(c.symbol)">
              <span class="chip-symbol">{{ c.symbol }}</span>
              <span class="chip-name">{{ c.name }}</span>
            </button>
          </div>
        </el-tab-pane>
      </el-tabs>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStockStore } from '@/store/stockStore'
import MarketOverview from '@/components/market/MarketOverview.vue'
import Heatmap from '@/components/market/Heatmap.vue'
import StateBlock from '@/components/common/StateBlock.vue'
import DataQualityBar from '@/components/common/DataQualityBar.vue'
import ModuleGuide from '@/components/common/ModuleGuide.vue'

const router = useRouter()
const store = useStockStore()
const activeCategory = ref('etfs')

const marketData = computed(() => store.marketData)
const marketMeta = computed(() => store.marketMeta)
const marketError = computed(() => store.marketError)
const marketLoading = computed(() => store.marketLoading)
const categories = computed(() => store.categories)

const quickAssets = [
  { symbol: 'SPY', name: 'S&P 500' },
  { symbol: 'QQQ', name: 'NASDAQ 100' },
  { symbol: 'NVDA', name: 'NVIDIA' },
  { symbol: 'AAPL', name: 'Apple' },
]

function goToStock(symbol) {
  router.push(`/stock/${encodeURIComponent(symbol)}`)
}

onMounted(() => {
  store.fetchMarketOverview()
  store.fetchCategories()
})
</script>

<style lang="scss" scoped>
.dashboard {
  max-width: 1440px;
  margin: 0 auto;
}

.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
  margin-bottom: 16px;
}

.eyebrow {
  color: $color-accent;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  margin-bottom: 4px;
}

.page-head h1 {
  color: $text-primary;
  font-size: 24px;
  margin-bottom: 6px;
}

.page-head p:last-child,
.section-row span {
  color: $text-secondary;
  font-size: 13px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(360px, 1fr) minmax(300px, 0.8fr);
  gap: 16px;
  margin: 18px 0;
}

.panel {
  background: $bg-card;
  border: 1px solid $border-color;
  border-radius: $radius-lg;
  padding: 16px;
}

.panel-title,
.section-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.panel-title h2,
.section-heading {
  color: $text-primary;
  font-size: 16px;
  font-weight: 700;
}

.quick-list {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin-top: 12px;
}

.quick-list button,
.symbol-chip {
  border: 1px solid $border-color;
  background: $bg-secondary;
  color: $text-primary;
  border-radius: $radius-md;
  cursor: pointer;
  text-align: left;
  transition: border-color $transition-fast, background $transition-fast;
}

.quick-list button {
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.quick-list button:hover,
.symbol-chip:hover {
  border-color: $color-accent;
  background: rgba(74, 142, 255, 0.08);
}

.quick-list strong,
.chip-symbol {
  color: $color-accent;
  font-weight: 700;
}

.quick-list span,
.chip-name {
  color: $text-secondary;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hot-section,
.category-section {
  margin-top: 18px;
}

.symbol-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 10px;
  padding: 8px 0;
}

.symbol-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
}

.chip-symbol {
  min-width: 70px;
}

@media (max-width: 1000px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .quick-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
