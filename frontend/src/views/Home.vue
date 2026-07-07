<template>
  <div class="dashboard">
    <header class="page-header">
      <h1 class="page-title">{{ t('dashboard.title') }}</h1>
      <span class="page-subtitle">{{ t('dashboard.subtitle') }}</span>
    </header>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon stat-icon--primary">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ stats.device_count }}</span>
          <span class="stat-label">{{ t('dashboard.totalDevices') }}</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon stat-icon--warning">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ stats.unacknowledged_alerts }}</span>
          <span class="stat-label">{{ t('dashboard.activeAlerts') }}</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon stat-icon--danger">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ stats.risk_devices }}</span>
          <span class="stat-label">{{ t('dashboard.riskDevices') }}</span>
        </div>
      </div>
    </div>

    <div class="quick-actions">
      <h2 class="section-title">{{ t('dashboard.quickActions') }}</h2>
      <div class="actions-grid">
        <router-link to="/devices" class="action-card">
          <svg class="action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <span class="action-label">{{ t('dashboard.scanNetwork') }}</span>
          <span class="action-desc">{{ t('dashboard.scanDesc') }}</span>
        </router-link>
        <router-link to="/alerts" class="action-card">
          <svg class="action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          <span class="action-label">{{ t('dashboard.viewAlerts') }}</span>
          <span class="action-desc">{{ t('dashboard.alertDesc') }}</span>
        </router-link>
      </div>
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
      stats: { device_count: 0, unacknowledged_alerts: 0, risk_devices: 0 }
    }
  },
  mounted() {
    this.loadStats()
  },
  methods: {
    async loadStats() {
      try {
        const res = await api.get('/system/stats')
        this.stats = res.data
      } catch (e) {
        console.error('Failed to load stats:', e)
      }
    }
  }
}
</script>

<style scoped>
.dashboard {
  max-width: 100%;
}

.page-header {
  margin-bottom: var(--space-xl);
}

.page-title {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 600;
  letter-spacing: -0.6px;
  color: var(--color-ink);
  margin-bottom: var(--space-xxs);
}

.page-subtitle {
  font-size: 14px;
  color: var(--color-ink-subtle);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-md);
  margin-bottom: var(--space-xl);
}

.stat-card {
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
  transition: all var(--transition-fast);
}

.stat-card:hover {
  border-color: var(--color-hairline-strong);
  background: var(--color-surface-2);
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon svg {
  width: 20px;
  height: 20px;
}

.stat-icon--primary {
  background: rgba(94, 106, 210, 0.15);
  color: var(--color-primary);
}

.stat-icon--warning {
  background: rgba(245, 158, 11, 0.15);
  color: var(--color-warning);
}

.stat-icon--danger {
  background: rgba(239, 68, 68, 0.15);
  color: var(--color-danger);
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-value {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 600;
  letter-spacing: -1px;
  color: var(--color-ink);
  line-height: 1;
}

.stat-label {
  font-size: 13px;
  color: var(--color-ink-subtle);
}

.section-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -0.3px;
  color: var(--color-ink-muted);
  margin-bottom: var(--space-md);
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-md);
}

.action-card {
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  text-decoration: none;
  transition: all var(--transition-fast);
}

.action-card:hover {
  border-color: var(--color-primary);
  background: var(--color-surface-2);
}

.action-icon {
  width: 32px;
  height: 32px;
  color: var(--color-primary);
}

.action-label {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-ink);
}

.action-desc {
  font-size: 13px;
  color: var(--color-ink-subtle);
}

@media (max-width: 768px) {
  .page-title {
    font-size: 24px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .stat-card {
    padding: var(--space-md);
  }

  .stat-icon {
    width: 36px;
    height: 36px;
  }

  .stat-icon svg {
    width: 18px;
    height: 18px;
  }

  .stat-value {
    font-size: 28px;
  }

  .actions-grid {
    grid-template-columns: 1fr;
  }
}
</style>
