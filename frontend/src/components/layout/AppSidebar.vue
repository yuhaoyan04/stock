<template>
  <aside class="app-sidebar" :class="{ collapsed }">
    <div v-if="!collapsed" class="workspace-card">
      <span>Workspace</span>
      <strong>Global Markets</strong>
      <small>Research · Backtest · Learn</small>
    </div>

    <el-menu :default-active="activeMenu" :collapse="collapsed" @select="handleSelect">
      <div v-if="!collapsed" class="nav-section">研究工作流</div>
      <el-menu-item index="/">
        <el-icon><DataAnalysis /></el-icon>
        <span>市场</span>
      </el-menu-item>
      <el-menu-item index="/compare">
        <el-icon><TrendCharts /></el-icon>
        <span>资产对比</span>
      </el-menu-item>
      <el-menu-item index="/portfolio">
        <el-icon><PieChart /></el-icon>
        <span>组合</span>
      </el-menu-item>
      <el-menu-item index="/simulation">
        <el-icon><Money /></el-icon>
        <span>模拟</span>
      </el-menu-item>
      <el-menu-item index="/research">
        <el-icon><Star /></el-icon>
        <span>研究</span>
      </el-menu-item>

      <div v-if="!collapsed" class="nav-section">资讯与学习</div>
      <el-menu-item index="/news">
        <el-icon><Document /></el-icon>
        <span>财经政策</span>
      </el-menu-item>
      <el-menu-item index="/learning">
        <el-icon><Reading /></el-icon>
        <span>金融课堂</span>
      </el-menu-item>

      <el-sub-menu v-if="!collapsed" index="assets">
        <template #title>
          <el-icon><Coin /></el-icon>
          <span>资产池</span>
        </template>
        <el-menu-item v-for="item in quickAssets" :key="item.symbol" :index="`/stock/${encodeURIComponent(item.symbol)}`">
          {{ item.symbol }} - {{ item.name }}
        </el-menu-item>
      </el-sub-menu>
    </el-menu>

    <div v-if="!collapsed" class="risk-note">
      <span>Non-advisory</span>
      <small>历史数据与课程内容仅用于研究和教育。</small>
    </div>

    <div class="sidebar-toggle" @click="collapsed = !collapsed">
      <el-icon><ArrowLeft v-if="!collapsed" /><ArrowRight v-else /></el-icon>
    </div>
  </aside>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const collapsed = ref(false)

const activeMenu = computed(() => {
  if (route.path.startsWith('/portfolio')) return '/portfolio'
  if (route.path.startsWith('/compare')) return '/compare'
  if (route.path.startsWith('/simulation')) return '/simulation'
  if (route.path.startsWith('/research')) return '/research'
  if (route.path.startsWith('/news')) return '/news'
  if (route.path.startsWith('/learning')) return '/learning'
  return '/'
})

const quickAssets = [
  { symbol: 'SPY', name: 'S&P 500' },
  { symbol: 'QQQ', name: 'NASDAQ 100' },
  { symbol: 'DIA', name: 'Dow Jones' },
  { symbol: 'IWM', name: 'Russell 2000' },
  { symbol: '^VIX', name: 'VIX' },
  { symbol: 'GLD', name: 'Gold' },
  { symbol: 'CL=F', name: 'Oil' },
  { symbol: 'BTC-USD', name: 'Bitcoin' },
]

function handleSelect(index) {
  router.push(index)
}
</script>

<style lang="scss" scoped>
.app-sidebar {
  width: $sidebar-width;
  flex-shrink: 0;
  background: linear-gradient(180deg, $bg-secondary, $bg-primary);
  border-right: 1px solid rgba(109, 125, 151, 0.2);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
  transition: width $transition-normal;
  position: relative;
  padding: 14px 10px 0;
}

.app-sidebar.collapsed {
  width: $sidebar-collapsed;
}

.workspace-card {
  margin: 0 2px 12px;
  padding: 14px;
  border: 1px solid rgba(138, 180, 255, 0.18);
  border-radius: $radius-lg;
  background: linear-gradient(135deg, rgba(79, 140, 255, 0.14), rgba(18, 185, 129, 0.07)), $bg-card;
  box-shadow: 0 14px 32px rgba(0, 0, 0, 0.2);
}

.workspace-card span {
  color: $color-accent-light;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
}

.workspace-card strong {
  display: block;
  color: $text-primary;
  font-size: 16px;
  margin: 5px 0 4px;
}

.workspace-card small {
  color: $text-muted;
  font-size: 12px;
}

.nav-section {
  color: $text-muted;
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
  padding: 16px 12px 7px;
}

.risk-note {
  margin: 12px 2px;
  padding: 12px;
  border-radius: $radius-md;
  border: 1px solid rgba(246, 183, 60, 0.2);
  background: rgba(246, 183, 60, 0.07);
}

.risk-note span {
  color: $color-warning;
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
}

.risk-note small {
  display: block;
  color: $text-secondary;
  line-height: 1.45;
  margin-top: 5px;
}

.sidebar-toggle {
  position: sticky;
  bottom: 0;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $bg-primary;
  border-top: 1px solid rgba(109, 125, 151, 0.18);
  cursor: pointer;
  color: $text-muted;
  transition: color $transition-fast;
  margin: 0 -10px;
}

.sidebar-toggle:hover {
  color: $text-primary;
}

.el-menu {
  flex: 1;
  border-right: 0;
  background: transparent;
}

.el-menu :deep(.el-menu-item),
.el-menu :deep(.el-sub-menu__title) {
  height: 42px;
  margin: 2px 0;
  border-radius: $radius-md;
}

.el-menu :deep(.el-menu-item.is-active) {
  background: rgba(79, 140, 255, 0.14);
  box-shadow: inset 3px 0 0 $color-accent;
}

.el-menu :deep(.el-menu-item:hover),
.el-menu :deep(.el-sub-menu__title:hover) {
  background: rgba(79, 140, 255, 0.08);
}

.el-menu .el-icon {
  font-size: 18px;
  margin-right: 8px;
}
</style>
