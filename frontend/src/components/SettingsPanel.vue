<template>
  <transition name="panel">
    <div v-if="visible" class="settings-overlay" @click.self="$emit('close')">
      <div class="settings-panel">
        <div class="panel-header">
          <h2 class="panel-title">设置</h2>
          <button class="panel-close" @click="$emit('close')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <div class="panel-content">
          <section class="settings-section">
            <h3 class="section-title">主题</h3>
            <ThemeSwitcher :current-mode="themeMode" @change="setThemeMode" />
          </section>

          <section class="settings-section">
            <h3 class="section-title">自定义颜色</h3>
            <ColorPicker
              label="主题色"
              :model-value="customColors.primary"
              @update:model-value="(v) => setCustomColor('primary', v)"
            />
          </section>

          <section class="settings-section">
            <button class="reset-btn" @click="resetColors">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
              </svg>
              恢复默认颜色
            </button>
          </section>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>
import ThemeSwitcher from './ThemeSwitcher.vue'
import ColorPicker from './ColorPicker.vue'
import { useTheme } from '@/composables/useTheme'

export default {
  components: { ThemeSwitcher, ColorPicker },
  props: {
    visible: { type: Boolean, default: false }
  },
  emits: ['close'],
  setup() {
    const { mode, customColors, setMode, setCustomColor, resetColors } = useTheme()
    return { themeMode: mode, customColors, setThemeMode: setMode, setCustomColor, resetColors }
  }
}
</script>

<style scoped>
.settings-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
  animation: fadeIn 150ms ease-out;
}

.settings-panel {
  width: 320px;
  max-width: 100%;
  height: 100%;
  background: var(--color-surface-1);
  border-left: 1px solid var(--color-hairline);
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  animation: slideLeft 200ms ease-out;
}

@keyframes slideLeft {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-lg);
  border-bottom: 1px solid var(--color-hairline);
}

.panel-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink);
}

.panel-close {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-ink-subtle);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.panel-close:hover {
  background: var(--color-surface-3);
  color: var(--color-ink);
}

.panel-close svg {
  width: 18px;
  height: 18px;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-lg);
}

.settings-section {
  margin-bottom: var(--space-xl);
}

.settings-section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-ink-subtle);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: var(--space-md);
}

.reset-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-ink-subtle);
  font-size: 13px;
  font-family: var(--font-body);
  cursor: pointer;
  transition: all var(--transition-fast);
  width: 100%;
}

.reset-btn:hover {
  background: var(--color-surface-2);
  border-color: var(--color-hairline-strong);
  color: var(--color-ink);
}

.reset-btn svg {
  width: 16px;
  height: 16px;
}

/* Transitions */
.panel-enter-active,
.panel-leave-active {
  transition: opacity 150ms ease;
}

.panel-enter-from,
.panel-leave-to {
  opacity: 0;
}
</style>
