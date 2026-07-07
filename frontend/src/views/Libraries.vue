<template>
  <div class="libraries">
    <header class="page-header">
      <div class="header-left">
        <h1 class="page-title">{{ t('libraries.title') }}</h1>
        <span class="page-subtitle">{{ t('libraries.subtitle') }}</span>
      </div>
      <button class="btn btn--primary" @click="updateAll" :disabled="updatingAll">
        <svg v-if="!updatingAll" class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <svg v-else class="btn-icon btn-icon--spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        {{ updatingAll ? t('libraries.updating') : t('libraries.updateAll') }}
      </button>
    </header>

    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-label">{{ t('libraries.totalEntries') }}</span>
        <span class="stat-value">{{ totalEntries.toLocaleString() }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">{{ t('libraries.lastFullUpdate') }}</span>
        <span class="stat-value">{{ lastFullUpdate || '-' }}</span>
      </div>
    </div>

    <div class="library-list">
      <div
        v-for="lib in libraries"
        :key="lib.id"
        class="library-card"
        :class="{ 'library-card--updating': updatingId === lib.id }"
      >
        <div class="library-icon" :class="'library-icon--' + lib.type">
          <svg v-if="lib.type === 'oui'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <svg v-else-if="lib.type === 'vendor'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
          <svg v-else-if="lib.type === 'merged'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M4 7v10c0 2 4 3 8 3s8-1 8-3V7M4 7c0 2 4 3 8 3s8-1 8-3M4 7c0-2 4-3 8-3s8 1 8 3m0 5c0 2-4 3-8 3s-8-1-8-3" />
          </svg>
        </div>

        <div class="library-info">
          <div class="library-header">
            <span class="library-name">{{ lib.name }}</span>
            <span class="library-status" :class="'status--' + lib.status">
              {{ t('libraries.status.' + lib.status) }}
            </span>
          </div>
          <span class="library-desc">{{ lib.description }}</span>
          <div class="library-meta">
            <span class="meta-item">
              <svg class="meta-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              {{ lib.entries.toLocaleString() }} {{ t('libraries.entries') }}
            </span>
            <span class="meta-item" v-if="lib.lastUpdate">
              <svg class="meta-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {{ formatDate(lib.lastUpdate) }}
            </span>
            <span class="meta-item meta-item--source">
              {{ lib.source }}
            </span>
          </div>
        </div>

        <div class="library-actions">
          <button
            v-if="lib.autoUpdate"
            class="btn btn--ghost btn--sm"
            @click="updateLibrary(lib)"
            :disabled="updatingId === lib.id"
          >
            <svg v-if="updatingId !== lib.id" class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <svg v-else class="btn-icon btn-icon--spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {{ updatingId === lib.id ? t('libraries.updating') : t('libraries.update') }}
          </button>
          <span v-else class="local-only-tag">{{ t('libraries.localOnly') }}</span>
        </div>
      </div>
    </div>

    <div v-if="updateResult" class="update-result" :class="'result--' + updateResult.type">
      <div class="result-content">
        <svg v-if="updateResult.type === 'success'" class="result-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <svg v-else class="result-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span class="result-message">{{ updateResult.message }}</span>
      </div>
      <button class="result-close" @click="updateResult = null">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script>
import { useI18n } from 'vue-i18n'
import api from '@/api'

export default {
  setup() {
    const { t } = useI18n()
    return { t }
  },
  data() {
    return {
      libraries: [],
      totalEntries: 0,
      lastFullUpdate: null,
      updatingAll: false,
      updatingId: null,
      updateResult: null
    }
  },
  mounted() {
    this.loadLibraries()
  },
  methods: {
    async loadLibraries() {
      try {
        const res = await api.get('/libraries/status')
        this.libraries = res.data.libraries
        this.totalEntries = res.data.totalEntries
        this.lastFullUpdate = res.data.lastFullUpdate
      } catch (e) {
        console.error('Failed to load libraries:', e)
      }
    },
    async updateAll() {
      this.updatingAll = true
      this.updateResult = null
      try {
        const res = await api.post('/libraries/update/oui_all')
        if (res.data.success) {
          this.updateResult = { type: 'success', message: res.data.message || this.t('libraries.updateSuccess') }
          await this.loadLibraries()
        } else {
          this.updateResult = { type: 'error', message: res.data.error || this.t('libraries.updateFailed') }
        }
      } catch (e) {
        this.updateResult = { type: 'error', message: this.t('libraries.updateFailed') }
      } finally {
        this.updatingAll = false
        setTimeout(() => { this.updateResult = null }, 8000)
      }
    },
    async updateLibrary(lib) {
      this.updatingId = lib.id
      this.updateResult = null
      try {
        const res = await api.post(`/libraries/update/${lib.id}`)
        if (res.data.success) {
          this.updateResult = { type: 'success', message: res.data.message || `${lib.name} ${this.t('libraries.updated')}` }
          await this.loadLibraries()
        } else {
          this.updateResult = { type: 'error', message: res.data.error || this.t('libraries.updateFailed') }
        }
      } catch (e) {
        this.updateResult = { type: 'error', message: this.t('libraries.updateFailed') }
      } finally {
        this.updatingId = null
        setTimeout(() => { this.updateResult = null }, 8000)
      }
    },
    formatDate(isoString) {
      if (!isoString) return '-'
      const d = new Date(isoString)
      const pad = n => String(n).padStart(2, '0')
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
    }
  }
}
</script>

<style scoped>
.libraries {
  max-width: 100%;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--space-xl);
  gap: var(--space-md);
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: var(--space-xxs);
}

.page-title {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 600;
  letter-spacing: -0.6px;
  color: var(--color-ink);
}

.page-subtitle {
  font-size: 14px;
  color: var(--color-ink-subtle);
}

.stats-bar {
  display: flex;
  gap: var(--space-xl);
  padding: var(--space-md) var(--space-lg);
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-xl);
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: 12px;
  color: var(--color-ink-subtle);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink);
}

.library-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.library-card {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-lg);
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  transition: all var(--transition-fast);
}

.library-card:hover {
  border-color: var(--color-hairline-strong);
  background: var(--color-surface-2);
}

.library-card--updating {
  border-color: var(--color-primary);
  background: rgba(94, 106, 210, 0.05);
}

.library-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.library-icon svg {
  width: 22px;
  height: 22px;
}

.library-icon--oui {
  background: rgba(94, 106, 210, 0.15);
  color: var(--color-primary);
}

.library-icon--vendor {
  background: rgba(39, 166, 68, 0.15);
  color: var(--color-success);
}

.library-icon--merged {
  background: rgba(245, 158, 11, 0.15);
  color: var(--color-warning);
}

.library-icon--mapping {
  background: rgba(139, 92, 246, 0.15);
  color: #8b5cf6;
}

.library-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-xxs);
}

.library-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.library-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-ink);
}

.library-status {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.status--active {
  background: rgba(39, 166, 68, 0.15);
  color: var(--color-success);
}

.status--empty {
  background: rgba(245, 158, 11, 0.15);
  color: var(--color-warning);
}

.status--missing {
  background: rgba(239, 68, 68, 0.15);
  color: var(--color-danger);
}

.library-desc {
  font-size: 13px;
  color: var(--color-ink-subtle);
}

.library-meta {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-top: var(--space-xxs);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--color-ink-tertiary);
}

.meta-icon {
  width: 14px;
  height: 14px;
}

.meta-item--source {
  color: var(--color-ink-subtle);
}

.library-actions {
  flex-shrink: 0;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: 8px 16px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  border: none;
  white-space: nowrap;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn--primary {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.btn--primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.btn--ghost {
  background: transparent;
  border: 1px solid var(--color-hairline);
  color: var(--color-ink-muted);
}

.btn--ghost:hover:not(:disabled) {
  border-color: var(--color-hairline-strong);
  color: var(--color-ink);
  background: var(--color-surface-2);
}

.btn--sm {
  padding: 6px 12px;
  font-size: 12px;
}

.btn-icon {
  width: 16px;
  height: 16px;
}

.btn-icon--spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.local-only-tag {
  font-size: 12px;
  color: var(--color-ink-tertiary);
  padding: 6px 12px;
}

.update-result {
  position: fixed;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-lg);
  border-radius: var(--radius-lg);
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
  box-shadow: var(--shadow-lg);
  max-width: 480px;
  z-index: 100;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

.result--success {
  border-left: 3px solid var(--color-success);
}

.result--error {
  border-left: 3px solid var(--color-danger);
}

.result-content {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.result-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.result--success .result-icon {
  color: var(--color-success);
}

.result--error .result-icon {
  color: var(--color-danger);
}

.result-message {
  font-size: 13px;
  color: var(--color-ink);
}

.result-close {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  color: var(--color-ink-subtle);
  cursor: pointer;
  flex-shrink: 0;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.result-close:hover {
  background: var(--color-surface-3);
  color: var(--color-ink);
}

.result-close svg {
  width: 14px;
  height: 14px;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
  }

  .page-title {
    font-size: 24px;
  }

  .stats-bar {
    flex-direction: column;
    gap: var(--space-md);
  }

  .library-card {
    flex-wrap: wrap;
    padding: var(--space-md);
  }

  .library-meta {
    flex-wrap: wrap;
    gap: var(--space-sm);
  }

  .library-actions {
    width: 100%;
    margin-top: var(--space-sm);
  }

  .library-actions .btn {
    width: 100%;
    justify-content: center;
  }

  .update-result {
    left: var(--space-md);
    right: var(--space-md);
    max-width: none;
    transform: none;
  }

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(16px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
}
</style>
