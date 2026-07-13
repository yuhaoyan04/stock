<template>
  <div class="learning-page">
    <section class="page-header">
      <div>
        <p class="eyebrow">Financial Learning</p>
        <h1>金融课堂</h1>
        <p>从概念、传导机制和风险出发理解市场。课程用于教育，不提供买卖建议。</p>
      </div>
    </section>

    <ModuleGuide
      title="金融课堂"
      description="先从一个概念开始，再通过关联 ticker 把理论与市场数据连接起来。"
      :steps="['优先阅读中文官方/交易所投教卡片。', '遇到英文或日文材料，可点击翻译获得中文辅助阅读。', '点击 ticker 打开行情详情，或阅读外部来源原文。']"
      note="翻译只用于降低阅读门槛，严谨表述请以原文为准。"
      class="mb-4"
    />
    <DataQualityBar class="mb-4" :meta="meta" />
    <StateBlock v-if="error" type="error" title="课程加载失败" :description="error">
      <template #action><el-button size="small" @click="load">重试</el-button></template>
    </StateBlock>

    <template v-else>
      <el-alert
        title="课程来源包含中国投资者网、交易所投教、监管/公共教育资源与 Wikipedia CC BY-SA 内容；不构成投资建议。"
        type="warning"
        :closable="false"
        show-icon
        class="mb-4"
      />
      <section class="learning-metrics mb-4">
        <article>
          <span>课程卡片</span>
          <strong>{{ lessons.length }}</strong>
          <small>覆盖基础、进阶和风险主题</small>
        </article>
        <article>
          <span>中文来源</span>
          <strong>{{ chineseCount }}</strong>
          <small>国内投教与交易所资源优先</small>
        </article>
        <article>
          <span>主题分类</span>
          <strong>{{ Math.max(categories.length - 1, 0) }}</strong>
          <small>股票、基金、期货、宏观、风险等</small>
        </article>
        <article>
          <span>已翻译</span>
          <strong>{{ translatedCount }}</strong>
          <small>外文材料辅助阅读</small>
        </article>
      </section>
      <el-radio-group v-model="category" size="small" class="filters">
        <el-radio-button v-for="item in categories" :key="item" :label="item">{{ item }}</el-radio-button>
      </el-radio-group>
      <StateBlock v-if="!loading && !filtered.length" type="empty" title="暂无课程" description="请稍后刷新。" />

      <div v-else class="lesson-grid">
        <article v-for="lesson in filtered" :key="lesson.id" class="lesson-card">
          <div class="lesson-meta">
            <div>
              <el-tag size="small" effect="plain">{{ lesson.category }}</el-tag>
              <el-tag v-if="lesson.language" size="small" effect="plain" type="info">{{ languageLabel(lesson.language) }}</el-tag>
            </div>
            <span>{{ lesson.level }}</span>
          </div>
          <h2>{{ lesson.translatedTitle || lesson.title }}</h2>
          <p>{{ lesson.translatedSummary || lesson.summary }}</p>
          <ul>
            <li v-for="takeaway in lesson.translatedTakeaways || lesson.takeaways" :key="takeaway">{{ takeaway }}</li>
          </ul>
          <div class="lesson-actions">
            <div class="symbols">
              <button v-for="symbol in lesson.marketLinks" :key="symbol" @click="$router.push(`/stock/${encodeURIComponent(symbol)}`)">
                {{ symbol }}
              </button>
            </div>
            <div class="links">
              <el-button size="small" text :loading="translating[lesson.id]" @click="translateLesson(lesson)">
                {{ lesson.isTranslated ? '已翻译' : '翻译' }}
              </el-button>
              <a :href="lesson.sourceUrl" target="_blank" rel="noopener noreferrer">
                {{ lesson.sourceName }} <el-icon><TopRight /></el-icon>
              </a>
            </div>
          </div>
        </article>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getApiErrorMessage, getLearningLessons, translateTexts } from '@/api'
import DataQualityBar from '@/components/common/DataQualityBar.vue'
import StateBlock from '@/components/common/StateBlock.vue'
import ModuleGuide from '@/components/common/ModuleGuide.vue'

const lessons = ref([])
const categories = ref(['全部'])
const category = ref('全部')
const meta = ref({})
const error = ref('')
const loading = ref(false)
const translating = reactive({})

const filtered = computed(() => (category.value === '全部' ? lessons.value : lessons.value.filter((item) => item.category === category.value)))
const chineseCount = computed(() => lessons.value.filter((item) => item.language === 'zh-CN').length)
const translatedCount = computed(() => lessons.value.filter((item) => item.isTranslated).length)

function languageLabel(language) {
  const labels = { 'zh-CN': '中文', en: '英文', ja: '日文', unknown: '未知语言' }
  return labels[language] || language || '未知语言'
}

async function translateLesson(lesson) {
  if (lesson.isTranslated) return
  translating[lesson.id] = true
  try {
    const sourceTakeaways = Array.isArray(lesson.takeaways) ? lesson.takeaways : []
    const res = await translateTexts([lesson.title, lesson.summary || '', ...sourceTakeaways])
    if (!res.data.available) {
      ElMessage.warning(res.meta?.warnings?.[0] || '未配置翻译服务，已保留原文')
      return
    }
    const [title, summary, ...takeaways] = res.data.translations
    const translatedTakeaways = takeaways.length ? takeaways : sourceTakeaways
    if (!hasVisibleTranslation([lesson.title, lesson.summary || '', ...sourceTakeaways], [title || '', summary || '', ...translatedTakeaways])) {
      ElMessage.warning('翻译服务返回了原文，暂未更新卡片')
      return
    }
    applyLessonTranslation(lesson.id, title || lesson.title, summary || lesson.summary, translatedTakeaways)
    ElMessage.success('翻译已更新')
  } catch (e) {
    ElMessage.error(getApiErrorMessage(e, '翻译失败，请稍后重试'))
  } finally {
    translating[lesson.id] = false
  }
}

function normalizeText(value) {
  return String(value || '').replace(/\s+/g, ' ').trim().toLowerCase()
}

function hasVisibleTranslation(originalTexts, translatedTexts) {
  return translatedTexts.some((text, index) => normalizeText(text) && normalizeText(text) !== normalizeText(originalTexts[index]))
}

function applyLessonTranslation(id, title, summary, takeaways) {
  lessons.value = lessons.value.map((entry) => {
    if (entry.id !== id) return entry
    return {
      ...entry,
      translatedTitle: title,
      translatedSummary: summary,
      translatedTakeaways: takeaways,
      isTranslated: true,
      language: 'zh-CN',
    }
  })
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const res = await getLearningLessons()
    lessons.value = res.data.lessons || []
    categories.value = res.data.categories || ['全部']
    meta.value = res.meta || {}
  } catch (e) {
    error.value = getApiErrorMessage(e, '课程内容暂时不可用')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style lang="scss" scoped>
.learning-page { max-width: 1480px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-end; margin-bottom: 18px; }
.eyebrow { color: $color-accent; font-size: 12px; font-weight: 700; }
.page-header h1 { font-size: 24px; color: $text-primary; margin: 4px 0 6px; }
.page-header p, .lesson-card > p { color: $text-secondary; line-height: 1.55; }
.learning-metrics { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.learning-metrics article {
  border: 1px solid rgba(109, 125, 151, 0.2);
  background: rgba(21, 28, 39, 0.72);
  border-radius: $radius-lg;
  padding: 15px;
}
.learning-metrics span { color: $text-muted; font-size: 12px; font-weight: 700; }
.learning-metrics strong { display: block; color: $text-primary; font-size: 26px; margin: 5px 0 3px; font-variant-numeric: tabular-nums; }
.learning-metrics small { color: $text-secondary; line-height: 1.35; }
.filters { margin-bottom: 16px; }
.lesson-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.lesson-card {
  background: rgba(21, 28, 39, 0.76);
  border: 1px solid rgba(109, 125, 151, 0.2);
  border-radius: $radius-lg;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: border-color $transition-fast, background $transition-fast, transform $transition-fast;
}
.lesson-card:hover { border-color: rgba(79, 140, 255, 0.58); background: rgba(29, 39, 52, 0.82); transform: translateY(-1px); }
.lesson-meta, .lesson-actions { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.lesson-meta > div { display: flex; flex-wrap: wrap; gap: 6px; }
.lesson-meta span { color: $text-muted; font-size: 12px; }
.lesson-card h2 { color: $text-primary; font-size: 17px; line-height: 1.45; }
.lesson-card ul { padding-left: 18px; color: $text-secondary; line-height: 1.7; }
.lesson-actions { margin-top: auto; align-items: flex-end; }
.symbols, .links { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.symbols button { border: 1px solid rgba(79, 140, 255, 0.24); background: rgba(79, 140, 255, 0.08); color: $color-accent-light; border-radius: $radius-sm; padding: 4px 7px; cursor: pointer; }
.links a { display: flex; align-items: center; gap: 4px; font-size: 12px; }
@media (max-width: 800px) {
  .learning-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .lesson-grid { grid-template-columns: 1fr; }
  .lesson-actions { align-items: flex-start; flex-direction: column; }
}
@media (max-width: 560px) {
  .learning-metrics { grid-template-columns: 1fr; }
}
</style>
