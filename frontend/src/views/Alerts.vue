<template>
  <div class="alerts-page">
    <header class="page-header">
      <div class="header-left">
        <h1 class="page-title">{{ t('alerts.title') }}</h1>
        <span class="page-subtitle">{{ t('alerts.subtitle', { count: alerts.length }) }}</span>
      </div>
      <button class="btn btn-secondary" @click="loadAlerts">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        {{ t('alerts.refresh') }}
      </button>
    </header>

    <!-- Desktop Table -->
    <div class="table-container desktop-only">
      <table class="data-table">
        <thead>
          <tr>
            <th>{{ t('alerts.severity') }}</th>
            <th>{{ t('alerts.type') }}</th>
            <th>{{ t('alerts.message') }}</th>
            <th>{{ t('alerts.time') }}</th>
            <th>{{ t('alerts.action') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="alert in alerts" :key="alert.id" class="table-row">
            <td>
              <span class="severity-badge" :class="'severity--' + alert.severity.toLowerCase()">
                {{ alert.severity }}
              </span>
            </td>
            <td class="cell-type">{{ alert.alert_type }}</td>
            <td class="cell-message">{{ alert.message }}</td>
            <td class="cell-time">{{ formatTime(alert.created_at) }}</td>
            <td>
              <button
                v-if="!alert.acknowledged"
                class="btn btn-sm btn-ghost"
                @click="acknowledgeAlert(alert.id)"
              >
                {{ t('alerts.acknowledge') }}
              </button>
              <span v-else class="acknowledged">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M5 13l4 4L19 7" />
                </svg>
                {{ t('alerts.acknowledged') }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Mobile Cards -->
    <div class="card-list mobile-only">
      <div v-for="alert in alerts" :key="alert.id" class="alert-card">
        <div class="card-header">
          <span class="severity-badge" :class="'severity--' + alert.severity.toLowerCase()">
            {{ alert.severity }}
          </span>
          <span class="card-time">{{ formatTime(alert.created_at) }}</span>
        </div>
        <div class="card-body">
          <div class="card-type">{{ alert.alert_type }}</div>
          <div class="card-message">{{ alert.message }}</div>
        </div>
        <div class="card-footer">
          <button
            v-if="!alert.acknowledged"
            class="btn btn-sm btn-primary"
            @click="acknowledgeAlert(alert.id)"
          >
            {{ t('alerts.acknowledge') }}
          </button>
          <span v-else class="acknowledged">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 13l4 4L19 7" />
            </svg>
            {{ t('alerts.acknowledged') }}
          </span>
        </div>
      </div>
    </div>

    <div v-if="alerts.length === 0 && !loading" class="empty-state">
      <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>
      <p class="empty-text">{{ t('alerts.noAlerts') }}</p>
      <p class="empty-hint">{{ t('alerts.noAlertsHint') }}</p>
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
      alerts: [],
      loading: false
    }
  },
  mounted() {
    this.loadAlerts()
  },
  methods: {
    async loadAlerts() {
      this.loading = true
      try {
        const res = await api.get('/alerts/')
        this.alerts = res.data
      } catch (e) {
        console.error('Failed to load alerts:', e)
      } finally {
        this.loading = false
      }
    },
    async acknowledgeAlert(id) {
      try {
        await api.put(`/alerts/${id}/ack`)
        await this.loadAlerts()
      } catch (e) {
        console.error('Failed to acknowledge alert:', e)
      }
    },
    formatTime(t) {
      if (!t) return '--'
      return new Date(t).toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
  }
}
</script>

<style scoped>
.alerts-page {
  max-width: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-lg);
  gap: var(--space-md);
  flex-wrap: wrap;
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

.btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: 8px 14px;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  font-family: var(--font-body);
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.btn svg {
  width: 16px;
  height: 16px;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}

.btn-primary {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.btn-primary:hover {
  background: var(--color-primary-hover);
}

.btn-secondary {
  background: var(--color-surface-2);
  color: var(--color-ink);
  border: 1px solid var(--color-hairline);
}

.btn-secondary:hover {
  background: var(--color-surface-3);
  border-color: var(--color-hairline-strong);
}

.btn-ghost {
  background: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
}

.btn-ghost:hover {
  background: rgba(94, 106, 210, 0.1);
}

.table-container {
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  padding: 12px 16px;
  text-align: left;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-ink-subtle);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background: var(--color-surface-2);
  border-bottom: 1px solid var(--color-hairline);
}

.data-table td {
  padding: 12px 16px;
  font-size: 14px;
  color: var(--color-ink-muted);
  border-bottom: 1px solid var(--color-hairline);
}

.table-row:hover {
  background: var(--color-surface-2);
}

.table-row:last-child td {
  border-bottom: none;
}

.cell-type {
  color: var(--color-ink);
  font-weight: 500;
}

.cell-message {
  color: var(--color-ink-muted);
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-time {
  color: var(--color-ink-tertiary);
  font-size: 13px;
}

.severity-badge {
  display: inline-flex;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.severity--info {
  background: var(--color-surface-3);
  color: var(--color-ink-subtle);
}

.severity--warning {
  background: rgba(245, 158, 11, 0.15);
  color: var(--color-warning);
}

.severity--critical {
  background: rgba(239, 68, 68, 0.15);
  color: var(--color-danger);
}

.acknowledged {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--color-success);
}

.acknowledged svg {
  width: 14px;
  height: 14px;
}

.card-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.alert-card {
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md);
  background: var(--color-surface-2);
  border-bottom: 1px solid var(--color-hairline);
}

.card-time {
  font-size: 12px;
  color: var(--color-ink-tertiary);
}

.card-body {
  padding: var(--space-md);
}

.card-type {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: var(--space-xs);
}

.card-message {
  font-size: 14px;
  color: var(--color-ink-muted);
  line-height: 1.5;
}

.card-footer {
  padding: var(--space-md);
  border-top: 1px solid var(--color-hairline);
  display: flex;
  justify-content: flex-end;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-xxl);
  text-align: center;
}

.empty-icon {
  width: 48px;
  height: 48px;
  color: var(--color-ink-tertiary);
  margin-bottom: var(--space-md);
}

.empty-text {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-ink-muted);
  margin-bottom: var(--space-xs);
}

.empty-hint {
  font-size: 14px;
  color: var(--color-ink-subtle);
}

.desktop-only {
  display: block;
}

.mobile-only {
  display: none;
}

@media (max-width: 768px) {
  .desktop-only {
    display: none !important;
  }

  .mobile-only {
    display: flex !important;
  }

  .page-header {
    flex-direction: column;
  }

  .page-title {
    font-size: 24px;
  }
}
</style>
