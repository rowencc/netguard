import { reactive, computed } from 'vue'

const STORAGE_KEY = 'netguard-theme'
const CUSTOM_COLORS_KEY = 'netguard-custom-colors'

const defaultColors = {
  primary: '#6366f1',
  success: '#22c55e',
  warning: '#f59e0b',
  danger: '#ef4444',
}

const state = reactive({
  mode: 'system',
  customColors: { ...defaultColors },
})

function getSystemTheme() {
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
    return 'light'
  }
  return 'dark'
}

function getEffectiveTheme() {
  if (state.mode === 'system') {
    return getSystemTheme()
  }
  return state.mode
}

function applyTheme() {
  const theme = getEffectiveTheme()
  document.documentElement.setAttribute('data-theme', theme)
  document.documentElement.className = `theme-${theme}`

  Object.entries(state.customColors).forEach(([key, value]) => {
    document.documentElement.style.setProperty(`--color-${key}`, value)
  })

  const hex = state.customColors.primary
  if (hex && hex.length === 7) {
    const r = parseInt(hex.slice(1, 3), 16)
    const g = parseInt(hex.slice(3, 5), 16)
    const b = parseInt(hex.slice(5, 7), 16)
    document.documentElement.style.setProperty('--color-primary-rgb', `${r}, ${g}, ${b}`)
  }
}

function setMode(newMode) {
  state.mode = newMode
  localStorage.setItem(STORAGE_KEY, newMode)
  applyTheme()
}

function setCustomColor(key, value) {
  state.customColors[key] = value
  localStorage.setItem(CUSTOM_COLORS_KEY, JSON.stringify(state.customColors))
  applyTheme()
}

function resetColors() {
  state.customColors = { ...defaultColors }
  localStorage.setItem(CUSTOM_COLORS_KEY, JSON.stringify(state.customColors))
  applyTheme()
}

function toggleTheme() {
  const current = getEffectiveTheme()
  setMode(current === 'dark' ? 'light' : 'dark')
}

let initialized = false

export function useTheme() {
  if (!initialized) {
    initialized = true

    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      state.mode = saved
    }

    const savedColors = localStorage.getItem(CUSTOM_COLORS_KEY)
    if (savedColors) {
      try {
        state.customColors = { ...defaultColors, ...JSON.parse(savedColors) }
      } catch (e) {}
    }

    applyTheme()

    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', () => {
        if (state.mode === 'system') {
          applyTheme()
        }
      })
    }
  }

  const mode = computed(() => state.mode)
  const customColors = computed(() => ({ ...state.customColors }))

  return {
    mode,
    customColors,
    setMode,
    setCustomColor,
    resetColors,
    toggleTheme,
  }
}
