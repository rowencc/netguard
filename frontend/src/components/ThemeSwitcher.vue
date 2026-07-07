<template>
  <div class="theme-switcher">
    <button
      v-for="option in themeOptions"
      :key="option.value"
      class="theme-btn"
      :class="{ active: currentMode === option.value }"
      @click="$emit('change', option.value)"
      :title="option.label"
    >
      <span class="theme-icon" v-html="option.icon"></span>
      <span class="theme-label">{{ option.label }}</span>
    </button>
  </div>
</template>

<script>
export default {
  props: {
    currentMode: { type: String, default: 'system' }
  },
  emits: ['change'],
  data() {
    return {
      themeOptions: [
        {
          value: 'light',
          label: '亮色',
          icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="5"/><path d="M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72l1.42 1.42M1 12h2m18 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
        },
        {
          value: 'dark',
          label: '暗色',
          icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>'
        },
        {
          value: 'system',
          label: '跟随系统',
          icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><path d="M8 21h8m-4-4v4"/></svg>'
        }
      ]
    }
  }
}
</script>

<style scoped>
.theme-switcher {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: var(--color-surface-2);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-hairline);
}

.theme-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-ink-subtle);
  font-size: 13px;
  font-family: var(--font-body);
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.theme-btn:hover {
  color: var(--color-ink);
  background: var(--color-surface-3);
}

.theme-btn.active {
  color: var(--color-on-primary);
  background: var(--color-primary);
  box-shadow: var(--shadow-sm);
}

.theme-icon {
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.theme-icon :deep(svg) {
  width: 100%;
  height: 100%;
}

.theme-label {
  display: none;
}

@media (min-width: 480px) {
  .theme-label {
    display: inline;
  }
}
</style>
