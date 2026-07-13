<template>
  <div class="state-block" :class="[`state-${type}`, compact ? 'is-compact' : '']">
    <el-icon class="state-icon">
      <Loading v-if="type === 'loading'" />
      <WarningFilled v-else-if="type === 'error'" />
      <InfoFilled v-else-if="type === 'warning'" />
      <DocumentRemove v-else />
    </el-icon>
    <div class="state-copy">
      <strong>{{ title }}</strong>
      <span v-if="description">{{ description }}</span>
    </div>
    <div v-if="$slots.action" class="state-action">
      <slot name="action" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  type: { type: String, default: 'empty' },
  title: { type: String, required: true },
  description: { type: String, default: '' },
  compact: { type: Boolean, default: false },
})
</script>

<style lang="scss" scoped>
.state-block {
  min-height: 150px;
  padding: 22px;
  border: 1px solid $border-color;
  border-radius: $radius-md;
  background: $bg-card;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  color: $text-secondary;
}

.state-block.is-compact {
  min-height: auto;
  padding: 10px 12px;
  justify-content: flex-start;
}

.state-icon {
  font-size: 24px;
  color: $text-muted;
}

.state-error .state-icon { color: $color-down; }
.state-warning .state-icon { color: $color-warning; }
.state-loading .state-icon { color: $color-accent; }

.state-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.state-copy strong {
  color: $text-primary;
  font-size: 14px;
}

.state-copy span {
  color: $text-secondary;
  font-size: 13px;
}

.state-action {
  margin-left: 8px;
}
</style>
