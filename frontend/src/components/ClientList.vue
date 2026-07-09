<template>
  <div class="client-list">
    <h3 class="client-title">{{ t('clients.title') }}</h3>
    <div v-if="clients.length === 0" class="client-empty">
      {{ t('clients.noClients') }}
    </div>
    <div v-else class="client-items">
      <div
        v-for="client in clients"
        :key="client.client_id"
        class="client-item"
        :class="{ 'client-selected': selectedClientId === client.client_id }"
        @click="$emit('select', client.client_id)"
      >
        <div class="client-status" :class="client.is_online ? 'status-online' : 'status-offline'"></div>
        <div class="client-info">
          <div class="client-name">{{ client.hostname || client.client_id }}</div>
          <div class="client-meta">
            {{ client.ip_address }} · {{ client.platform || 'unknown' }}
            <span v-if="client.version" class="client-version">v{{ client.version }}</span>
          </div>
        </div>
        <div class="client-stats">
          <span class="stat">{{ client.device_count || 0 }} {{ t('clients.devices') }}</span>
          <button
            v-if="needsUpgrade(client)"
            class="btn-upgrade"
            @click.stop="showUpgradeGuide(client)"
            :title="t('clients.upgradeNeeded')"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;">
              <path d="M12 9v6m3-3H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            {{ t('clients.upgrade') }}
          </button>
        </div>
      </div>
    </div>

    <!-- 升级指南弹窗 -->
    <div v-if="upgradeClient" class="upgrade-modal" @click.self="upgradeClient = null">
      <div class="upgrade-content">
        <div class="upgrade-header">
          <h3>{{ t('clients.upgradeTitle') }}</h3>
          <button class="btn-close" @click="upgradeClient = null">&times;</button>
        </div>
        <div class="upgrade-body">
          <p class="upgrade-desc">{{ t('clients.upgradeDesc') }}</p>

          <div class="upgrade-step">
            <span class="step-num">1</span>
            <span>{{ t('clients.upgradeStep1') }}</span>
          </div>
          <div class="code-block">
            <code>curl -fsSL https://raw.githubusercontent.com/rowencc/netguard/main/client/upgrade.sh | bash</code>
            <button class="btn-copy" @click="copyUpgradeCmd">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"></path>
              </svg>
            </button>
          </div>

          <div class="upgrade-step">
            <span class="step-num">2</span>
            <span>{{ t('clients.upgradeStep2') }}</span>
          </div>
          <div class="code-block">
            <code>~/.netguard/start.sh</code>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useI18n } from 'vue-i18n'

export default {
  setup() {
    const { t } = useI18n()
    return { t }
  },
  props: {
    clients: { type: Array, default: () => [] },
    selectedClientId: { type: String, default: '' }
  },
  emits: ['select'],
  data() {
    return {
      upgradeClient: null,
      currentVersion: '0.4.0', // 当前最新版本
    }
  },
  methods: {
    needsUpgrade(client) {
      if (!client.version) return false
      return this.compareVersion(client.version, this.currentVersion) < 0
    },
    compareVersion(v1, v2) {
      const parts1 = v1.split('.').map(Number)
      const parts2 = v2.split('.').map(Number)
      for (let i = 0; i < Math.max(parts1.length, parts2.length); i++) {
        const p1 = parts1[i] || 0
        const p2 = parts2[i] || 0
        if (p1 !== p2) return p1 - p2
      }
      return 0
    },
    showUpgradeGuide(client) {
      this.upgradeClient = client
    },
    copyUpgradeCmd() {
      const cmd = 'curl -fsSL https://raw.githubusercontent.com/rowencc/netguard/main/client/upgrade.sh | bash'
      navigator.clipboard.writeText(cmd)
    }
  }
}
</script>

<style scoped>
.client-list {
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
  margin-bottom: var(--space-lg);
}

.client-title {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink-muted);
  margin-bottom: var(--space-sm);
}

.client-empty {
  font-size: 13px;
  color: var(--color-ink-subtle);
  text-align: center;
  padding: var(--space-md);
}

.client-items {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.client-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 10px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  border: 1px solid transparent;
}

.client-item:hover {
  background: var(--color-surface-2);
}

.client-item.client-selected {
  background: rgba(94, 106, 210, 0.1);
  border-color: var(--color-primary-focus);
}

.client-status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-online {
  background: var(--color-success);
  box-shadow: 0 0 6px var(--color-success);
}

.status-offline {
  background: var(--color-ink-tertiary);
}

.client-info {
  flex: 1;
  min-width: 0;
}

.client-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.client-meta {
  font-size: 12px;
  color: var(--color-ink-subtle);
}

.client-version {
  margin-left: 4px;
  padding: 1px 6px;
  background: var(--color-surface-3);
  border-radius: var(--radius-sm);
  font-size: 10px;
  color: var(--color-ink-subtle);
}

.client-stats {
  font-size: 12px;
  color: var(--color-ink-subtle);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.stat {
  white-space: nowrap;
}

.btn-upgrade {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: var(--color-warning);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 11px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-upgrade:hover {
  opacity: 0.9;
  transform: scale(1.02);
}

/* Upgrade Modal */
.upgrade-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.upgrade-content {
  background: var(--color-surface-1);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 480px;
  max-height: 80vh;
  overflow-y: auto;
}

.upgrade-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1px solid var(--color-hairline);
}

.upgrade-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-ink);
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--color-ink-subtle);
  padding: 0;
  line-height: 1;
}

.btn-close:hover {
  color: var(--color-ink);
}

.upgrade-body {
  padding: var(--space-lg);
}

.upgrade-desc {
  font-size: 14px;
  color: var(--color-ink-subtle);
  margin-bottom: var(--space-lg);
}

.upgrade-step {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.step-num {
  width: 24px;
  height: 24px;
  background: var(--color-primary);
  color: var(--color-on-primary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.code-block {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  background: var(--color-surface-2);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  padding: 10px 12px;
  margin-bottom: var(--space-md);
  margin-left: 32px;
}

.code-block code {
  flex: 1;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--color-ink);
  word-break: break-all;
  user-select: all;
}

.btn-copy {
  padding: 6px;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: var(--color-ink-subtle);
  transition: all var(--transition-fast);
}

.btn-copy:hover {
  background: var(--color-surface-3);
  color: var(--color-primary);
}
</style>
