<template>
  <div class="color-picker-group">
    <label class="color-label">{{ label }}</label>
    <div class="color-presets">
      <button
        v-for="color in presetColors"
        :key="color"
        class="color-preset"
        :class="{ active: modelValue === color }"
        :style="{ backgroundColor: color }"
        @click="$emit('update:modelValue', color)"
      >
        <svg v-if="modelValue === color" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
          <path d="M5 13l4 4L19 7"/>
        </svg>
      </button>
      <label class="color-custom">
        <input
          type="color"
          :value="modelValue"
          @input="$emit('update:modelValue', $event.target.value)"
          class="color-input"
        />
        <span class="color-custom-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 8v8m-4-4h8"/>
          </svg>
        </span>
      </label>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    label: { type: String, required: true },
    modelValue: { type: String, required: true },
    presets: { type: Array, default: () => [] }
  },
  emits: ['update:modelValue'],
  computed: {
    presetColors() {
      return this.presets.length ? this.presets : [
        '#6366f1', '#8b5cf6', '#ec4899', '#ef4444',
        '#f97316', '#eab308', '#22c55e', '#14b8a6',
        '#06b6d4', '#3b82f6', '#64748b', '#78716c'
      ]
    }
  }
}
</script>

<style scoped>
.color-picker-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.color-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-ink-subtle);
}

.color-presets {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.color-preset {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  justify-content: center;
}

.color-preset:hover {
  transform: scale(1.1);
}

.color-preset.active {
  border-color: var(--color-ink);
  box-shadow: 0 0 0 2px var(--color-canvas);
}

.color-preset svg {
  width: 12px;
  height: 12px;
}

.color-custom {
  position: relative;
  width: 28px;
  height: 28px;
  cursor: pointer;
}

.color-input {
  position: absolute;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.color-custom-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px dashed var(--color-hairline-strong);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-ink-subtle);
  transition: all var(--transition-fast);
}

.color-custom:hover .color-custom-icon {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.color-custom-icon svg {
  width: 14px;
  height: 14px;
}
</style>
