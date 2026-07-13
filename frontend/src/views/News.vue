<template>
  <div class="news-page">
    <section class="page-header">
      <div>
        <p class="eyebrow">Daily Briefing</p>
        <h1>财经政策</h1>
        <p>聚合央行、国际组织与公开政策来源。标题与摘要仅用于研究导航，请以原文为准。</p>
      </div>
      <el-button :loading="loading" @click="load">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </section>

    <ModuleGuide
      title="财经政策"
      description="用这页建立宏观事件观察，不把单条新闻直接等同为交易信号。"
      :steps="['按地区或主题筛选当天资讯。', '核对媒体、发布时间、地区和数据源提示。', '外文内容可先翻译，再打开原文阅读上下文。']"
      note="仅展示公开标题、短摘要和原文链接；付费媒体正文不会在本产品中转载。"
      class="mb-4"
    />
    <DataQualityBar class="mb-4" :meta="meta" />
    <StateBlock v-if="error" type="error" title="资讯加载失败" :description="error">
      <template #action><el-button size="small" @click="load">重试</el-button></template>
    </StateBlock>

    <template v-else>
      <el-alert
        title="内容按公开 RSS 自动聚合；翻译仅作阅读辅助，正式含义请以原文为准。"
        type="info"
        :closable="false"
        show-icon
        class="mb-4"
      />

      <section class="briefing-metrics mb-4">
        <article>
          <span>资讯条目</span>
          <strong>{{ items.length }}</strong>
          <small>公开来源自动聚合</small>
        </article>
        <article>
          <span>覆盖来源</span>
          <strong>{{ sourceCount }}</strong>
          <small>央行、监管、国际组织与公开索引</small>
        </article>
        <article>
          <span>地区覆盖</span>
          <strong>{{ regionCount }}</strong>
          <small>美国、欧洲、日本、新加坡、香港等</small>
        </article>
        <article>
          <span>已翻译</span>
          <strong>{{ translatedCount }}</strong>
          <small>仅作辅助阅读</small>
        </article>
      </section>

      <section class="recommend-panel">
        <div class="panel-title">
          <h2>今日优先阅读</h2>
          <span>按时效与来源覆盖度排序</span>
        </div>
        <div class="recommend-grid">
          <article v-for="item in recommended" :key="item.id" class="recommend-card">
            <div class="tags">
              <span class="topic">{{ item.topic }}</span>
              <span>{{ item.region || '全球' }}</span>
              <span>{{ languageLabel(item.language) }}</span>
            </div>
            <h3>{{ item.translatedTitle || item.title }}</h3>
            <p>{{ item.translatedSummary || item.summary }}</p>
            <footer>
              <span>{{ item.source }} · {{ date(item.publishedAt) }}</span>
              <div class="actions">
                <el-button size="small" text :loading="translating[item.id]" @click="translateNews(item)">
                  {{ item.isTranslated ? '已翻译' : '翻译' }}
                </el-button>
                <a :href="item.url" target="_blank" rel="noopener noreferrer">
                  原文 <el-icon><TopRight /></el-icon>
                </a>
              </div>
            </footer>
          </article>
        </div>
      </section>

      <section class="feed-panel mt-4">
        <div class="panel-title">
          <h2>全部资讯</h2>
          <el-radio-group v-model="topic" size="small">
            <el-radio-button v-for="item in topics" :key="item" :label="item">{{ item }}</el-radio-button>
          </el-radio-group>
        </div>
        <StateBlock v-if="!loading && !filtered.length" type="empty" title="暂无该主题资讯" description="可切换主题或稍后刷新。" />
        <div v-else class="feed-list">
          <article v-for="item in filtered" :key="item.id" class="feed-row">
            <div>
              <div class="tags">
                <span class="topic">{{ item.topic }}</span>
                <span>{{ item.region || '全球' }}</span>
                <span>{{ languageLabel(item.language) }}</span>
              </div>
              <h3>{{ item.translatedTitle || item.title }}</h3>
              <p>{{ item.translatedSummary || item.summary }}</p>
            </div>
            <aside>
              <b>{{ item.source }}</b>
              <time>{{ date(item.publishedAt) }}</time>
              <el-button size="small" text :loading="translating[item.id]" @click="translateNews(item)">
                {{ item.isTranslated ? '已翻译' : '翻译' }}
              </el-button>
              <a :href="item.url" target="_blank" rel="noopener noreferrer">
                原文 <el-icon><TopRight /></el-icon>
              </a>
            </aside>
          </article>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getApiErrorMessage, getDailyBriefing, translateTexts } from '@/api'
import DataQualityBar from '@/components/common/DataQualityBar.vue'
import StateBlock from '@/components/common/StateBlock.vue'
import ModuleGuide from '@/components/common/ModuleGuide.vue'
import { formatDateTime } from '@/utils/formatters'

const items = ref([])
const recommended = ref([])
const topics = ref(['全部'])
const topic = ref('全部')
const meta = ref({})
const loading = ref(false)
const error = ref('')
const translating = reactive({})

const filtered = computed(() => (topic.value === '全部' ? items.value : items.value.filter((item) => item.topic === topic.value)))
const sourceCount = computed(() => new Set(items.value.map((item) => item.source).filter(Boolean)).size)
const regionCount = computed(() => new Set(items.value.map((item) => item.region).filter(Boolean)).size)
const translatedCount = computed(() => items.value.filter((item) => item.isTranslated).length)
const date = (value) => (value ? formatDateTime(value, '日期待发布') : '持续更新')

function languageLabel(language) {
  const labels = { 'zh-CN': '中文', en: '英文', ja: '日文', unknown: '未知语言' }
  return labels[language] || language || '未知语言'
}

async function translateNews(item) {
  if (item.isTranslated) return
  translating[item.id] = true
  try {
    const res = await translateTexts([item.title, item.summary || ''])
    if (!res.data.available) {
      ElMessage.warning(res.meta?.warnings?.[0] || '未配置翻译服务，已保留原文')
      return
    }
    const [title, summary] = res.data.translations
    if (!hasVisibleTranslation([item.title, item.summary || ''], [title || '', summary || ''])) {
      ElMessage.warning('翻译服务返回了原文，暂未更新卡片')
      return
    }
    applyNewsTranslation(item.id, title || item.title, summary || item.summary)
    ElMessage.success('翻译已更新')
  } catch (e) {
    ElMessage.error(getApiErrorMessage(e, '翻译失败，请稍后重试'))
  } finally {
    translating[item.id] = false
  }
}

function normalizeText(value) {
  return String(value || '').replace(/\s+/g, ' ').trim().toLowerCase()
}

function hasVisibleTranslation(originalTexts, translatedTexts) {
  return translatedTexts.some((text, index) => normalizeText(text) && normalizeText(text) !== normalizeText(originalTexts[index]))
}

function applyNewsTranslation(id, title, summary) {
  const update = (entry) => {
    if (entry.id !== id) return entry
    return {
      ...entry,
      translatedTitle: title,
      translatedSummary: summary,
      isTranslated: true,
      language: 'zh-CN',
    }
  }
  items.value = items.value.map(update)
  recommended.value = recommended.value.map(update)
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const res = await getDailyBriefing()
    items.value = res.data.items || []
    recommended.value = res.data.recommended || []
    topics.value = res.data.topics || ['全部']
    meta.value = res.meta || {}
  } catch (e) {
    error.value = getApiErrorMessage(e, '公开资讯源暂时不可用')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style lang="scss" scoped>
.news-page { max-width: 1480px; margin: 0 auto; }
.page-header, .panel-title { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }
.page-header { margin-bottom: 18px; }
.eyebrow, .topic { color: $color-accent; font-size: 12px; font-weight: 700; }
.page-header h1 { font-size: 24px; color: $text-primary; margin: 4px 0 6px; }
.page-header p, .panel-title span, .recommend-card p, .feed-row p { color: $text-secondary; line-height: 1.55; }
.briefing-metrics { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.briefing-metrics article {
  border: 1px solid rgba(109, 125, 151, 0.2);
  background: rgba(21, 28, 39, 0.72);
  border-radius: $radius-lg;
  padding: 15px;
}
.briefing-metrics span { color: $text-muted; font-size: 12px; font-weight: 700; }
.briefing-metrics strong { display: block; color: $text-primary; font-size: 26px; margin: 5px 0 3px; font-variant-numeric: tabular-nums; }
.briefing-metrics small { color: $text-secondary; line-height: 1.35; }
.recommend-panel, .feed-panel { border: 1px solid rgba(109, 125, 151, 0.2); background: rgba(21, 28, 39, 0.78); border-radius: $radius-lg; padding: 18px; }
.panel-title { align-items: center; margin-bottom: 14px; }
.panel-title h2 { color: $text-primary; font-size: 16px; }
.recommend-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.recommend-card, .feed-row {
  border: 1px solid rgba(109, 125, 151, 0.18);
  background: rgba(12, 18, 26, 0.58);
  border-radius: $radius-md;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: border-color $transition-fast, background $transition-fast;
}
.recommend-card:hover, .feed-row:hover { border-color: rgba(79, 140, 255, 0.7); background: rgba(29, 39, 52, 0.86); }
.recommend-card h3, .feed-row h3 { color: $text-primary; font-size: 15px; line-height: 1.45; }
.tags { display: flex; flex-wrap: wrap; gap: 8px; color: $text-muted; font-size: 12px; }
.recommend-card footer, .feed-row aside { color: $text-muted; font-size: 12px; display: flex; gap: 8px; margin-top: auto; }
.recommend-card footer { justify-content: space-between; align-items: center; }
.actions, .feed-row aside a { display: flex; align-items: center; gap: 6px; }
.feed-list { display: flex; flex-direction: column; gap: 8px; }
.feed-row { flex-direction: row; justify-content: space-between; }
.feed-row aside { min-width: 132px; flex-direction: column; align-items: flex-end; margin: 0; }
.feed-row aside b { color: $text-secondary; font-weight: 500; }
@media (max-width: 900px) {
  .briefing-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .recommend-grid { grid-template-columns: 1fr; }
  .feed-row, .recommend-card footer { flex-direction: column; }
  .feed-row aside { align-items: flex-start; }
}
@media (max-width: 560px) {
  .briefing-metrics { grid-template-columns: 1fr; }
}
</style>
