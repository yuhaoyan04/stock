<template>
  <div class="app-container" :class="`theme-${theme}`">
    <AppHeader @toggle-sidebar="sidebarOpen = !sidebarOpen" />
    <div class="app-body">
      <!-- 移动端遮罩 -->
      <div v-if="sidebarOpen" class="mobile-overlay" @click="sidebarOpen = false"></div>
      <AppSidebar :class="{ 'mobile-open': sidebarOpen }" @navigate="sidebarOpen = false" />
      <main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import { useTheme } from '@/utils/theme'

const { theme, applyTheme } = useTheme()
const sidebarOpen = ref(false)

onMounted(() => applyTheme(theme.value))
</script>

<style lang="scss" scoped>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(circle at 16% 8%, rgba(79, 140, 255, 0.14), transparent 28%),
    radial-gradient(circle at 88% 14%, rgba(18, 185, 129, 0.1), transparent 24%),
    linear-gradient(135deg, #070a0f 0%, #0a111b 48%, #090d13 100%);
}

.app-container.theme-light {
  background: linear-gradient(135deg, #f8fbff 0%, #edf3f9 48%, #f7fafc 100%);
}

.app-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  min-height: 0;
  position: relative;
}

/* ── 移动端遮罩 ──────────────────────────────── */
.mobile-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 150;
}

@media (max-width: 768px) {
  .mobile-overlay {
    display: block;
  }
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px 28px 32px;
  min-width: 0;
  position: relative;
}

.main-content::before {
  content: '';
  position: fixed;
  inset: $header-height 0 0 $sidebar-width;
  pointer-events: none;
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(180deg, rgba(255, 255, 255, 0.025) 1px, transparent 1px);
  background-size: 72px 72px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.5), transparent 70%);
}

@media (max-width: 768px) {
  .main-content::before { inset: $header-height 0 0 0; }
}

@media (max-width: 900px) {
  .main-content {
    padding: 18px 16px 28px;
  }
}

@media (max-width: 768px) {
  .main-content {
    padding: 14px 12px 24px;
  }
}
</style>
