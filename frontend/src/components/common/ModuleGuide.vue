<template>
  <el-collapse class="module-guide" v-model="open">
    <el-collapse-item :name="title">
      <template #title><el-icon><QuestionFilled /></el-icon><strong>如何使用{{ title }}</strong><span>{{ summary }}</span></template>
      <div class="guide-content"><p>{{ description }}</p><ol><li v-for="step in steps" :key="step">{{ step }}</li></ol><p v-if="note" class="guide-note">{{ note }}</p></div>
    </el-collapse-item>
  </el-collapse>
</template>
<script setup>
import { ref } from 'vue'
defineProps({ title:{type:String,required:true}, summary:{type:String,default:'展开查看操作步骤'}, description:{type:String,required:true}, steps:{type:Array,default:()=>[]}, note:{type:String,default:''} })
const open=ref([])
</script>
<style lang="scss" scoped>
.module-guide{border:1px solid $border-color;border-radius:$radius-md;background:$bg-card}.module-guide :deep(.el-collapse-item__header){background:transparent;border:0;color:$text-primary;padding:0 14px;gap:8px}.module-guide :deep(.el-collapse-item__wrap){background:transparent;border:0}.module-guide :deep(.el-collapse-item__content){padding:0 14px 14px}.module-guide span{color:$text-muted;font-size:12px;font-weight:400}.guide-content{color:$text-secondary;line-height:1.7}.guide-content ol{padding-left:20px;margin-top:8px}.guide-note{color:$color-warning;margin-top:8px}
</style>
