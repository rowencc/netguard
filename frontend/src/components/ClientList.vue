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
          <div class="client-meta">{{ client.ip_address }} · {{ client.platform || 'unknown' }}</div>
        </div>
        <div class="client-stats">
          <span class="stat">{{ client.device_count || 0 }} {{ t('clients.devices') }}</span>
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
  emits: ['select']
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

.client-stats {
  font-size: 12px;
  color: var(--color-ink-subtle);
}

.stat {
  white-space: nowrap;
}
</style>
