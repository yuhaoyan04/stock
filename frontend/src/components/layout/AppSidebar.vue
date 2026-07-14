<template>
  <aside class="app-sidebar" :class="{ collapsed, 'mobile-open': mobileOpen }">
    <!-- 移动端关闭按钮 -->
    <div class="mobile-close" @click="$emit('navigate')">
      <el-icon><Close /></el-icon>
    </div>

    <el-menu :default-active="activeMenu" :collapse="collapsed" @select="onSelect">
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
      <el-menu-item index="/guide">
        <el-icon><Compass /></el-icon>
        <span>指南</span>
      </el-menu-item>
      <el-menu-item index="/news">
        <el-icon><Document /></el-icon>
        <span>财经政策</span>
      </el-menu-item>
      <el-menu-item index="/learning">
        <el-icon><Reading /></el-icon>
        <span>金融课堂</span>
      </el-menu-item>

      <el-sub-menu index="assets" v-if="!collapsed">
        <template #title>
          <el-icon><Coin /></el-icon>
          <span>资产池</span>
        </template>
        <el-menu-item v-for="item in quickAssets" :key="item.symbol" :index="`/stock/${encodeURIComponent(item.symbol)}`">
          {{ item.symbol }} - {{ item.name }}
        </el-menu-item>
      </el-sub-menu>
    </el-menu>

    <div class="sidebar-toggle" @click="collapsed = !collapsed">
      <el-icon><ArrowLeft v-if="!collapsed" /><ArrowRight v-else /></el-icon>
    </div>
  </aside>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const props = defineProps({
  mobileOpen: { type: Boolean, default: false },
})

const emit = defineEmits(['navigate'])

const router = useRouter()
const route = useRoute()
const collapsed = ref(false)

const activeMenu = computed(() => {
  if (route.path.startsWith('/portfolio')) return '/portfolio'
  if (route.path.startsWith('/compare')) return '/compare'
  if (route.path.startsWith('/simulation')) return '/simulation'
  if (route.path.startsWith('/research')) return '/research'
  if (route.path.startsWith('/guide')) return '/guide'
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

function onSelect(index) {
  router.push(index)
  emit('navigate')
}
</script>

<style lang="scss" scoped>
.app-sidebar {
  width: $sidebar-width;
  flex-shrink: 0;
  background-color: $bg-secondary;
  border-right: 1px solid $border-color;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
  transition: width $transition-normal, transform $transition-normal;
  position: relative;
}

.app-sidebar.collapsed { width: $sidebar-collapsed; }

/* ── 移动端：隐藏侧边栏，overlay 滑入 ─────────── */
.mobile-close {
  display: none;
  justify-content: flex-end;
  padding: 14px 16px 4px;
  color: $text-muted;
  cursor: pointer;
}

@media (max-width: 768px) {
  .app-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 200;
    transform: translateX(-100%);
    box-shadow: none;
  }

  .app-sidebar.mobile-open {
    transform: translateX(0);
    box-shadow: $shadow-lg;
  }

  .mobile-close {
    display: flex;
  }

  .sidebar-toggle {
    display: none;
  }
}

.sidebar-toggle { position: sticky; bottom: 0; height: 40px; display: flex; align-items: center; justify-content: center; background-color: $bg-secondary; border-top: 1px solid $border-color; cursor: pointer; color: $text-muted; transition: color $transition-fast; }
.sidebar-toggle:hover { color: $text-primary; }
.el-menu { flex: 1; border-right: 0; }
.el-menu .el-icon { font-size: 18px; margin-right: 8px; }
</style>
