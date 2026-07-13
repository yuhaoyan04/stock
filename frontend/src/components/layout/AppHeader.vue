<template>
  <header class="app-header">
    <div class="header-left">
      <div class="logo" @click="$router.push('/')">
        <svg class="logo-icon" viewBox="0 0 36 36" width="36" height="36">
          <rect width="36" height="36" rx="8" fill="#111827"/>
          <path d="M8 23 L14 12 L19 19 L24 8 L29 23" stroke="#8ab4ff" stroke-width="2.7" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M8 27 H29" stroke="#12b981" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <div class="brand-copy">
          <span class="logo-text">Stock<span class="logo-accent">Research</span></span>
          <small>Investment Workbench</small>
        </div>
      </div>
    </div>

    <div class="header-center">
      <el-icon class="search-prefix"><Search /></el-icon>
      <StockSearch @select="goToStock" />
    </div>

    <div class="header-right">
      <div class="source-status">
        <span class="status-dot"></span>
        <div>
          <strong>{{ sourceLabel }}</strong>
          <small>{{ updatedLabel }}</small>
        </div>
      </div>
      <el-tooltip :content="theme === 'dark' ? '切换亮色主题' : '切换暗色主题'" placement="bottom">
        <el-button class="theme-toggle" circle size="small" @click="toggleTheme">
          <el-icon><Sunny v-if="theme === 'dark'" /><Moon v-else /></el-icon>
        </el-button>
      </el-tooltip>
      <el-button-group class="nav-btns">
        <el-button :type="route.name === 'Dashboard' ? 'primary' : 'default'" size="small" @click="$router.push('/')">市场</el-button>
        <el-button :type="route.name === 'Compare' ? 'primary' : 'default'" size="small" @click="$router.push('/compare')">对比</el-button>
      </el-button-group>
      <div class="session-chip">Research Mode</div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import StockSearch from '@/components/stock/StockSearch.vue'
import { useStockStore } from '@/store/stockStore'
import { formatDateTime } from '@/utils/formatters'
import { useTheme } from '@/utils/theme'

const router = useRouter()
const route = useRoute()
const store = useStockStore()
const { theme, toggleTheme } = useTheme()

const sourceLabel = computed(() => store.marketMeta?.source || 'yfinance')
const updatedLabel = computed(() => formatDateTime(store.marketMeta?.last_updated, '等待刷新'))

function goToStock(symbol) {
  router.push(`/stock/${encodeURIComponent(symbol)}`)
}
</script>

<style lang="scss" scoped>
.app-header {
  height: $header-height;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 22px;
  background: var(--app-header-bg);
  border-bottom: 1px solid rgba(109, 125, 151, 0.22);
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.22);
  backdrop-filter: blur(18px);
  flex-shrink: 0;
  z-index: 100;
}
.header-left { display: flex; align-items: center; min-width: 250px; }
.logo { display: flex; align-items: center; gap: 10px; cursor: pointer; }
.logo-icon { flex-shrink: 0; border: 1px solid rgba(138, 180, 255, 0.28); border-radius: 9px; box-shadow: 0 10px 28px rgba(79, 140, 255, 0.18); }
.brand-copy { display: flex; flex-direction: column; line-height: 1.1; }
.brand-copy small { color: $text-muted; font-size: 11px; margin-top: 3px; }
.logo-text { font-size: 18px; font-weight: 760; color: $text-primary; }
.logo-accent { color: $color-accent; }
.header-center {
  flex: 1;
  max-width: 620px;
  margin: 0 26px;
  position: relative;
}
.search-prefix {
  position: absolute;
  left: 13px;
  top: 50%;
  transform: translateY(-50%);
  color: $text-muted;
  z-index: 2;
}
.header-center :deep(.el-select .el-input__wrapper) {
  min-height: 42px;
  padding-left: 32px;
  background: $bg-input;
  border: 1px solid rgba(138, 180, 255, 0.18);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03), 0 12px 30px rgba(0, 0, 0, 0.16);
  border-radius: 8px;
}
.header-right { display: flex; align-items: center; gap: 12px; min-width: 300px; justify-content: flex-end; }
.source-status { display: flex; align-items: center; gap: 8px; color: $text-secondary; min-width: 140px; padding: 8px 10px; border: 1px solid rgba(109, 125, 151, 0.18); border-radius: $radius-md; background: $bg-card; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: $color-up; box-shadow: 0 0 0 3px $color-up-bg; }
.source-status div { display: flex; flex-direction: column; line-height: 1.15; }
.source-status strong { color: $text-primary; font-size: 12px; font-weight: 600; }
.source-status small { color: $text-muted; font-size: 11px; white-space: nowrap; }
.nav-btns .el-button { border-color: rgba(109, 125, 151, 0.22); background-color: $bg-card; color: $text-secondary; }
.nav-btns .el-button:hover { border-color: $color-accent; color: $text-primary; }
.nav-btns .el-button.el-button--primary { background-color: $color-accent; border-color: $color-accent; color: #fff; }
.session-chip { color: $color-up; font-size: 12px; font-weight: 700; padding: 8px 10px; border: 1px solid rgba(18, 185, 129, 0.22); border-radius: $radius-md; background: rgba(18, 185, 129, 0.08); }
.theme-toggle { border-color: rgba(109, 125, 151, 0.22); background: $bg-card; color: $text-secondary; }
.theme-toggle:hover { color: $color-accent; border-color: $color-accent; }
@media (max-width: 1160px) { .source-status, .session-chip { display: none; } .header-right { min-width: 140px; } }
@media (max-width: 820px) { .header-left { min-width: 48px; } .brand-copy { display: none; } .header-center { margin: 0 12px; } .nav-btns { display: none; } }
</style>
