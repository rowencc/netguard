<template>
  <div class="devices-page">
    <!-- MAC Lookup -->
    <div class="lookup-section">
      <h2 class="lookup-title">{{ t('devices.lookupTitle') }}</h2>
      <div class="lookup-input-group">
        <input
          v-model="lookupMac"
          class="lookup-input"
          :placeholder="t('devices.lookupPlaceholder')"
          @keyup.enter="lookupDevice"
        />
        <button class="btn btn-primary" @click="lookupDevice" :disabled="!lookupMac.trim()">
          {{ t('devices.lookup') }}
        </button>
      </div>
      <div v-if="lookupResult" class="lookup-result">
        <div class="result-card" :class="'result--' + (lookupResult.device_type || 'unknown')">
          <div class="result-row">
            <span class="result-label">MAC</span>
            <code class="mono result-value">{{ lookupResult.mac_address }}</code>
          </div>
          <div class="result-row">
            <span class="result-label">{{ t('devices.vendor') }}</span>
            <span class="result-value">{{ lookupResult.vendor || '--' }}</span>
          </div>
          <div class="result-row">
            <span class="result-label">{{ t('devices.type') }}</span>
            <span class="tag" :class="getDeviceTypeClass(lookupResult.device_type)">
              {{ t('deviceTypes.' + lookupResult.device_type) || lookupResult.device_type }}
            </span>
          </div>
          <div class="result-row">
            <span class="result-label">{{ t('devices.risk') }}</span>
            <span class="risk-badge" :class="'risk--' + (lookupResult.risk_level || 'low').toLowerCase()">
              {{ t('riskLevels.' + (lookupResult.risk_level || 'low').toLowerCase()) || lookupResult.risk_level }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Client Selection -->
    <ClientList
      v-if="wsClients.length > 0"
      :clients="wsClients"
      :selected-client-id="selectedClientId"
      @select="selectClient"
    />

    <header class="page-header">
      <div class="header-left">
        <h1 class="page-title">{{ t('devices.title') }}</h1>
        <span class="page-subtitle">{{ t('devices.subtitle', { count: devices.length }) }}</span>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary" @click="loadDevices" :disabled="loading || checking">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {{ (loading || checking) ? t('devices.checking') : t('devices.refresh') }}
        </button>
        <button class="btn btn-primary" @click="scanNetwork" :disabled="scanning">
          <svg v-if="!scanning" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <span v-if="scanning" class="spinner"></span>
          {{ scanning ? t('devices.scanning') : t('devices.scan') }}
        </button>
      </div>
    </header>

    <div class="filters">
      <select class="filter-select" v-model="filterRisk" @change="loadDevices">
        <option value="">{{ t('devices.allRisk') }}</option>
        <option value="HIGH">{{ t('riskLevels.high') }}</option>
        <option value="MEDIUM">{{ t('riskLevels.medium') }}</option>
        <option value="LOW">{{ t('riskLevels.low') }}</option>
      </select>
    </div>

    <!-- Desktop Table -->
    <div class="table-container desktop-only">
      <table class="data-table">
        <thead>
          <tr>
            <th>{{ t('devices.ip') }}</th>
            <th>{{ t('devices.mac') }}</th>
            <th>{{ t('devices.name') }}</th>
            <th>{{ t('devices.vendor') }}</th>
            <th>{{ t('devices.type') }}</th>
            <th>{{ t('devices.risk') }}</th>
            <th>{{ t('devices.status') }}</th>
            <th>{{ t('devices.lastSeen') }}</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="device in displayDevices" :key="device.id || device.mac_address" class="table-row">
            <td><code class="mono">{{ device.ip_address }}</code></td>
            <td><code class="mono">{{ device.mac_address }}</code></td>
            <td class="cell-name">{{ device.hostname || '--' }}</td>
            <td class="cell-vendor" @click="startEdit(device, 'vendor')">
              <span v-if="editingDevice?.id === device.id && editingField === 'vendor'">
                <input v-model="editValue" class="inline-edit" @keyup.enter="saveEdit(device)" @keyup.escape="cancelEdit" ref="editInput" />
              </span>
              <span v-else :class="{ 'editable': true, 'unknown-value': !device.vendor }">
                {{ device.vendor || t('devices.clickToEdit') }}
              </span>
            </td>
            <td>
              <span v-if="editingDevice?.id === device.id && editingField === 'device_type'" class="inline-select-wrap">
                <select v-model="editValue" class="inline-edit" @change="saveEdit(device)" @keyup.escape="cancelEdit">
                  <option value="camera">{{ t('deviceTypes.camera') }}</option>
                  <option value="router">{{ t('deviceTypes.router') }}</option>
                  <option value="phone">{{ t('deviceTypes.phone') }}</option>
                  <option value="computer">{{ t('deviceTypes.computer') }}</option>
                  <option value="printer">{{ t('deviceTypes.printer') }}</option>
                  <option value="network_device">{{ t('deviceTypes.network_device') }}</option>
                  <option value="switch">{{ t('deviceTypes.switch') }}</option>
                  <option value="server">{{ t('deviceTypes.server') }}</option>
                  <option value="tv">{{ t('deviceTypes.tv') }}</option>
                  <option value="speaker">{{ t('deviceTypes.speaker') }}</option>
                  <option value="iot">{{ t('deviceTypes.iot') }}</option>
                  <option value="unknown">{{ t('deviceTypes.unknown') }}</option>
                </select>
              </span>
              <span v-else class="tag editable" :class="getDeviceTypeClass(device.device_type)" @click="startEdit(device, 'device_type')">
                {{ t('deviceTypes.' + device.device_type) || device.device_type || t('devices.clickToEdit') }}
              </span>
            </td>
            <td>
              <span class="risk-badge" :class="'risk--' + (device.risk_level || 'low').toLowerCase()">
                {{ t('riskLevels.' + (device.risk_level || 'low').toLowerCase()) || device.risk_level }}
              </span>
            </td>
            <td>
              <span class="status-indicator" :class="getOnlineStatus(device).class">
                {{ getOnlineStatus(device).text }}
              </span>
            </td>
            <td class="cell-time">{{ formatTime(device.last_seen) }}</td>
            <td class="cell-actions">
              <button v-if="editingDevice?.id === device.id" class="btn-icon btn-save" @click="saveEdit(device)" :title="t('devices.save')">&#10003;</button>
              <button v-if="editingDevice?.id === device.id" class="btn-icon btn-cancel" @click="cancelEdit" :title="t('devices.cancel')">&#10007;</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Mobile Cards -->
    <div class="card-list mobile-only">
      <div v-for="device in displayDevices" :key="device.id || device.mac_address" class="device-card">
        <div class="card-header">
          <code class="mono card-ip">{{ device.ip_address }}</code>
          <span class="risk-badge" :class="'risk--' + (device.risk_level || 'low').toLowerCase()">
            {{ t('riskLevels.' + (device.risk_level || 'low').toLowerCase()) || device.risk_level }}
          </span>
        </div>
        <div class="card-body">
          <div class="card-row">
            <span class="row-label">MAC</span>
            <code class="mono row-value">{{ device.mac_address }}</code>
          </div>
          <div class="card-row">
            <span class="row-label">{{ t('devices.name') }}</span>
            <span class="row-value">{{ device.hostname || '--' }}</span>
          </div>
          <div class="card-row">
            <span class="row-label">{{ t('devices.vendor') }}</span>
            <span class="row-value">{{ device.vendor || '--' }}</span>
          </div>
          <div class="card-row">
            <span class="row-label">{{ t('devices.type') }}</span>
            <span class="tag" :class="getDeviceTypeClass(device.device_type)">
              {{ t('deviceTypes.' + device.device_type) || device.device_type || 'unknown' }}
            </span>
          </div>
          <div class="card-row">
            <span class="row-label">{{ t('devices.status') }}</span>
            <span class="status-indicator" :class="getOnlineStatus(device).class">
              {{ getOnlineStatus(device).text }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="displayDevices.length === 0 && !loading" class="empty-state">
      <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>

      <!-- 无客户端代理连接 - 显示安装指南 -->
      <template v-if="scanError === 'no_client' || (!hasClient)">
        <p class="empty-text">{{ t('devices.noClientTitle') }}</p>
        <p class="empty-hint" style="margin-bottom: 20px;">{{ t('devices.noClientHint') }}</p>

        <div class="install-guide">
          <h3 class="guide-title">{{ t('devices.quickInstall') }}</h3>

          <!-- 一键安装命令 -->
          <div class="install-step">
            <div class="step-header">
              <span class="step-num">1</span>
              <span class="step-title">{{ t('devices.step1Title') }}</span>
            </div>
            <p class="step-desc">{{ t('devices.step1Desc') }}</p>
            <div class="code-block">
              <code>curl -fsSL https://net.soccn.com/install.sh | bash</code>
              <button class="btn-copy" @click="copyInstallCmd" :title="t('devices.copy')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                  <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"></path>
                </svg>
              </button>
            </div>
          </div>

          <!-- 安装说明 -->
          <div class="install-step">
            <div class="step-header">
              <span class="step-num">2</span>
              <span class="step-title">{{ t('devices.step2Title') }}</span>
            </div>
            <p class="step-desc">{{ t('devices.step2Desc') }}</p>
            <div class="code-block">
              <code>~/.netguard/start.sh</code>
            </div>
          </div>

          <!-- 管理命令 -->
          <div class="install-step">
            <div class="step-header">
              <span class="step-num">3</span>
              <span class="step-title">{{ t('devices.step3Title') }}</span>
            </div>
            <div class="cmd-list">
              <div class="cmd-item">
                <code>~/.netguard/start.sh</code>
                <span class="cmd-desc">{{ t('devices.cmdStart') }}</span>
              </div>
              <div class="cmd-item">
                <code>~/.netguard/stop.sh</code>
                <span class="cmd-desc">{{ t('devices.cmdStop') }}</span>
              </div>
              <div class="cmd-item">
                <code>~/.netguard/status.sh</code>
                <span class="cmd-desc">{{ t('devices.cmdStatus') }}</span>
              </div>
            </div>
          </div>

          <!-- 支持系统 -->
          <div class="support-info">
            <span class="support-badge">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
              </svg>
              {{ t('devices.supportedOS') }}
            </span>
          </div>
        </div>
      </template>

      <!-- 新会话，有客户端可用 -->
      <template v-else-if="isNewSession && hasClient">
        <p class="empty-text">{{ t('devices.newSessionHint') }}</p>
        <p class="empty-hint">{{ t('devices.newSessionSubHint') }}</p>
        <button class="btn btn-primary" @click="scanNetwork" :disabled="scanning" style="margin-top: 16px;">
          <svg v-if="!scanning" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:16px;height:16px;">
            <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <span v-if="scanning" class="spinner"></span>
          {{ scanning ? t('devices.scanning') : t('devices.startScan') }}
        </button>
      </template>

      <!-- 默认 -->
      <template v-else>
        <p class="empty-text">{{ t('devices.noDevices') }}</p>
        <p class="empty-hint">{{ t('devices.noDevicesHint') }}</p>
      </template>
    </div>
  </div>
</template>

<script>
import { useI18n } from 'vue-i18n'
import api from '@/api'
import { useWebSocket } from '@/composables/useWebSocket'
import ClientList from '@/components/ClientList.vue'

export default {
  components: { ClientList },
  setup() {
    const { t } = useI18n()
    const { connected, clients: wsClients, scanProgress, requestScan, onMessage } = useWebSocket()
    return { t, wsConnected: connected, wsClients, scanProgress, requestScan, onMessage }
  },
  data() {
    return {
      devices: [],
      scanning: false,
      loading: false,
      checking: false,
      isNewSession: false,
      scanError: '',
      copied: false,
      filterRisk: '',
      lookupMac: '',
      lookupResult: null,
      selectedClientId: '',
      scanDevices: [],
      scanId: null,
      removeWsHandler: null,
      editingDevice: null,
      editingField: '',
      editValue: '',
    }
  },
  computed: {
    displayDevices() {
      if (this.scanDevices.length > 0 && this.scanning) {
        return this.scanDevices
      }
      return this.devices
    },
    hasClient() {
      return this.wsClients.length > 0
    }
  },
  mounted() {
    const isRefresh = !!sessionStorage.getItem('netguard_devices_session')
    sessionStorage.setItem('netguard_devices_session', '1')

    if (isRefresh) {
      // Refresh: clear current devices and auto-trigger scan
      this.devices = []
      this.scanNetwork()
    } else {
      // New session: don't load devices, show empty state
      this.isNewSession = true
    }

    this.removeWsHandler = this.onMessage(this.handleWsMessage)

    // 监听客户端连接，清除错误状态并加载设备
    this._unwatchClients = this.$watch('wsClients', (newVal, oldVal) => {
      if (newVal.length > 0 && oldVal.length === 0) {
        this.scanError = ''
        // 客户端首次连接时，加载该客户端的设备
        this.loadDevices()
      }
    })
  },
  beforeUnmount() {
    if (this.removeWsHandler) {
      this.removeWsHandler()
    }
    if (this._unwatchClients) {
      this._unwatchClients()
    }
  },
  methods: {
    handleWsMessage(data) {
      if (data.type === 'scan_progress' && data.scan_id === this.scanId) {
        const progress = data.data
        if (progress.status === 'device_found') {
          const device = progress.device
          if (!this.scanDevices.find(d => d.mac_address === device.mac_address)) {
            this.scanDevices.push(device)
          }
        } else if (progress.status === 'complete') {
          this.scanning = false
          this.scanDevices = []
          this.scanId = null
          this.loadDevices()
        }
      }
    },
    selectClient(clientId) {
      this.selectedClientId = this.selectedClientId === clientId ? '' : clientId
      this.loadDevices()
    },
    async loadDevices() {
      this.loading = true
      this.isNewSession = false
      try {
        const params = { scan_source: 'client' }
        // 如果有选中的客户端或只有1个客户端，按客户端过滤
        const targetClientId = this.selectedClientId || (this.wsClients.length === 1 ? this.wsClients[0].client_id : '')
        if (targetClientId) {
          params.client_id = targetClientId
        }
        if (this.filterRisk) {
          params.risk_level = this.filterRisk
        }
        const res = await api.get('/devices/', { params })
        this.devices = res.data
        this.checkOnline()
      } catch (e) {
        console.error('Failed to load devices:', e)
      } finally {
        this.loading = false
      }
    },
    async checkOnline() {
      if (this.checking) return
      this.checking = true
      try {
        const res = await api.get('/devices/check-online')
        const statusMap = {}
        for (const d of res.data.devices) {
          statusMap[d.id] = d.is_online
        }
        this.devices = this.devices.map(dev => ({
          ...dev,
          _is_online: statusMap[dev.id] ?? false,
          _last_seen: statusMap[dev.id] ? new Date().toISOString() : dev.last_seen
        }))
      } catch (e) {
        console.error('Check online failed:', e)
      } finally {
        this.checking = false
      }
    },
    async lookupDevice() {
      const mac = this.lookupMac.trim()
      if (!mac) return
      try {
        const res = await api.get(`/devices/lookup/${encodeURIComponent(mac)}`)
        this.lookupResult = res.data
      } catch (e) {
        console.error('Lookup failed:', e)
        this.lookupResult = null
      }
    },
    startEdit(device, field) {
      this.editingDevice = device
      this.editingField = field
      this.editValue = device[field] || ''
    },
    cancelEdit() {
      this.editingDevice = null
      this.editingField = ''
      this.editValue = ''
    },
    async saveEdit(device) {
      if (!this.editValue.trim()) return
      try {
        await api.post('/corrections/correct', {
          mac_address: device.mac_address,
          field_name: this.editingField,
          new_value: this.editValue.trim(),
          old_value: device[this.editingField] || '',
        })
        device[this.editingField] = this.editValue.trim()
        this.cancelEdit()
        this.loadDevices()
      } catch (e) {
        console.error('Save correction failed:', e)
      }
    },
    async scanNetwork() {
      this.scanning = true
      this.scanDevices = []
      this.scanError = ''
      this.devices = [] // 清空当前设备列表，显示扫描进度

      // 优先使用客户端代理扫描（本地网络）
      const targetClientId = this.selectedClientId || (this.wsClients.length > 0 ? this.wsClients[0].client_id : '')
      if (targetClientId) {
        try {
          const res = await api.post('/devices/scan-client', {
            client_id: targetClientId,
          })
          this.scanId = res.data.scan_id
          return
        } catch (e) {
          console.error('Client scan failed:', e)
        }
      }

      // 没有客户端代理连接时，提示用户
      this.scanning = false
      this.scanError = 'no_client'
    },
    async scanServerSide() {
      try {
        await api.post('/devices/scan')
        await this.loadDevices()
      } catch (e) {
        console.error('Scan failed:', e)
      } finally {
        this.scanning = false
      }
    },
    getDeviceTypeClass(type) {
      const map = {
        camera: 'tag--danger',
        router: 'tag--primary',
        phone: 'tag--success',
        computer: 'tag--warning',
        printer: 'tag--warning',
        network_device: 'tag--primary',
        switch: 'tag--primary',
        server: 'tag--warning',
        tv: 'tag--info',
        speaker: 'tag--info',
        iot: 'tag--info'
      }
      return map[type] || 'tag--info'
    },
    getOnlineStatus(device) {
      if (device._is_online !== undefined) {
        return device._is_online
          ? { class: 'status--online', text: this.t('devices.online') }
          : { class: 'status--offline', text: this.t('devices.offline') }
      }
      if (device.is_online !== undefined) {
        return device.is_online
          ? { class: 'status--online', text: this.t('devices.online') }
          : { class: 'status--offline', text: this.t('devices.offline') }
      }
      if (!device.last_seen) {
        return { class: 'status--offline', text: this.t('devices.offline') }
      }
      const lastSeen = new Date(device.last_seen)
      const now = new Date()
      const diffMinutes = (now - lastSeen) / (1000 * 60)
      if (diffMinutes < 5) {
        return { class: 'status--online', text: this.t('devices.online') }
      } else if (diffMinutes < 60) {
        return { class: 'status--idle', text: this.t('devices.idle') }
      } else {
        return { class: 'status--offline', text: this.t('devices.offline') }
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
    },
    copyInstallCmd() {
      const cmd = 'curl -fsSL https://raw.githubusercontent.com/rowencc/netguard/main/client/install.sh | bash'
      navigator.clipboard.writeText(cmd).then(() => {
        this.copied = true
        setTimeout(() => { this.copied = false }, 2000)
      })
    }
  }
}
</script>

<style scoped>
.devices-page {
  max-width: 100%;
}

/* MAC Lookup Section */
.lookup-section {
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  margin-bottom: var(--space-lg);
}

.lookup-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -0.3px;
  color: var(--color-ink-muted);
  margin-bottom: var(--space-md);
}

.lookup-input-group {
  display: flex;
  gap: var(--space-sm);
}

.lookup-input {
  flex: 1;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-2);
  color: var(--color-ink);
  font-size: 14px;
  font-family: var(--font-mono);
  transition: all var(--transition-fast);
}

.lookup-input:focus {
  outline: none;
  border-color: var(--color-primary-focus);
  box-shadow: 0 0 0 2px rgba(94, 106, 210, 0.2);
}

.lookup-input::placeholder {
  color: var(--color-ink-tertiary);
  font-family: var(--font-body);
}

.lookup-result {
  margin-top: var(--space-md);
}

.result-card {
  background: var(--color-surface-2);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.result-card.result--camera { border-left: 3px solid var(--color-danger); }
.result-card.result--router { border-left: 3px solid var(--color-primary); }
.result-card.result--phone { border-left: 3px solid var(--color-success); }
.result-card.result--computer { border-left: 3px solid var(--color-warning); }
.result-card.result--iot { border-left: 3px solid var(--color-ink-subtle); }

.result-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid var(--color-hairline);
}

.result-row:last-child { border-bottom: none; }

.result-label { font-size: 13px; color: var(--color-ink-subtle); }
.result-value { font-size: 14px; color: var(--color-ink); font-weight: 500; }


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

.header-actions {
  display: flex;
  gap: var(--space-sm);
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

.btn svg { width: 16px; height: 16px; }

.btn-primary {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.btn-primary:hover:not(:disabled) { background: var(--color-primary-hover); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-secondary {
  background: var(--color-surface-2);
  color: var(--color-ink);
  border: 1px solid var(--color-hairline);
}

.btn-secondary:hover {
  background: var(--color-surface-3);
  border-color: var(--color-hairline-strong);
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.filters { margin-bottom: var(--space-md); }

.filter-select {
  padding: 8px 12px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-1);
  color: var(--color-ink);
  font-size: 14px;
  font-family: var(--font-body);
  min-width: 160px;
}

.filter-select:focus {
  outline: none;
  border-color: var(--color-primary-focus);
  box-shadow: 0 0 0 2px rgba(94, 106, 210, 0.2);
}

.table-container {
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.data-table { width: 100%; border-collapse: collapse; }

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
  padding: 12px 12px;
  font-size: 13px;
  color: var(--color-ink-muted);
  border-bottom: 1px solid var(--color-hairline);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.data-table th:nth-child(5),
.data-table td:nth-child(5) {
  min-width: 6em;
}

.data-table th:nth-child(7),
.data-table td:nth-child(7) {
  min-width: 5em;
}

.table-row:hover { background: var(--color-surface-2); }
.table-row:last-child td { border-bottom: none; }

.mono { font-family: var(--font-mono); font-size: 12px; }
.cell-name { color: var(--color-ink); font-weight: 500; max-width: 120px; }
.cell-vendor { color: var(--color-ink-subtle); max-width: 150px; }
.cell-time { color: var(--color-ink-tertiary); font-size: 12px; }

.cell-actions {
  width: 60px;
  text-align: center;
  white-space: nowrap;
}

.editable {
  cursor: pointer;
  position: relative;
  padding: 2px 4px;
  border-radius: var(--radius-xs);
  transition: all var(--transition-fast);
}

.editable::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 4px;
  right: 4px;
  height: 1px;
  background: currentColor;
  opacity: 0.3;
  transition: opacity var(--transition-fast);
}

.editable:hover {
  background: rgba(var(--color-primary-rgb), 0.1);
}

.editable:hover::after {
  opacity: 0;
}

.unknown-value {
  color: var(--color-ink-tertiary);
  font-style: italic;
  opacity: 0.7;
}

.inline-edit {
  padding: 6px 10px;
  border: 2px solid var(--color-primary);
  border-radius: var(--radius-md);
  font-size: 13px;
  font-family: var(--font-body);
  background: var(--color-surface-1);
  color: var(--color-ink);
  width: 140px;
  box-shadow: 0 0 0 3px rgba(var(--color-primary-rgb), 0.2);
  animation: editFocus 150ms ease-out;
}

@keyframes editFocus {
  from {
    box-shadow: 0 0 0 0px rgba(var(--color-primary-rgb), 0.3);
    transform: scale(0.98);
  }
  to {
    box-shadow: 0 0 0 3px rgba(var(--color-primary-rgb), 0.2);
    transform: scale(1);
  }
}

.inline-edit:focus {
  outline: none;
  border-color: var(--color-primary);
}

.inline-select-wrap .inline-edit {
  width: 120px;
  cursor: pointer;
}

.btn-icon {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
  animation: scaleIn 150ms ease-out;
}

.btn-save {
  background: var(--color-success);
  color: white;
  box-shadow: 0 2px 8px rgba(var(--color-success-rgb), 0.3);
}

.btn-save:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(var(--color-success-rgb), 0.4);
}

.btn-cancel {
  background: var(--color-surface-3);
  color: var(--color-ink-subtle);
  margin-left: 4px;
}

.btn-cancel:hover {
  background: var(--color-danger);
  color: white;
}

.tag {
  display: inline-flex;
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  font-size: 11px;
  font-weight: 500;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.tag--primary {
  background: rgba(var(--color-primary-rgb), 0.15);
  color: var(--color-primary);
}

.tag--success {
  background: rgba(var(--color-success-rgb), 0.15);
  color: var(--color-success);
}

.tag--warning {
  background: rgba(var(--color-warning-rgb), 0.15);
  color: var(--color-warning);
}

.tag--danger {
  background: rgba(var(--color-danger-rgb), 0.15);
  color: var(--color-danger);
}

.tag--info {
  background: var(--color-surface-3);
  color: var(--color-ink-subtle);
}

.risk-badge {
  display: inline-flex;
  padding: 3px 10px;
  border-radius: var(--radius-pill);
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  white-space: nowrap;
}

.risk--low {
  background: rgba(var(--color-success-rgb), 0.15);
  color: var(--color-success);
}
.risk--medium { background: rgba(245, 158, 11, 0.15); color: var(--color-warning); }
.risk--high {
  background: rgba(var(--color-danger-rgb), 0.15);
  color: var(--color-danger);
}

.risk--critical {
  background: var(--color-danger);
  color: white;
}

.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  white-space: nowrap;
}

.status-indicator::before {
  content: '';
  width: 8px;
  height: 8px;
  border-radius: 50%;
  box-shadow: 0 0 6px currentColor;
}

.status--online::before {
  background: var(--color-success);
  color: var(--color-success);
}

.status--idle::before {
  background: var(--color-warning);
  color: var(--color-warning);
}

.status--offline::before {
  background: var(--color-ink-tertiary);
  color: var(--color-ink-tertiary);
  box-shadow: none;
}

.card-list { display: flex; flex-direction: column; gap: var(--space-sm); }

.device-card {
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

.card-ip { font-size: 15px; font-weight: 500; color: var(--color-ink); }

.card-body { padding: var(--space-md); }

.card-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-hairline);
}

.card-row:last-child { border-bottom: none; }
.row-label { font-size: 13px; color: var(--color-ink-subtle); }
.row-value { font-size: 13px; color: var(--color-ink-muted); }

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

.empty-text { font-size: 16px; font-weight: 500; color: var(--color-ink-muted); margin-bottom: var(--space-xs); }
.empty-hint { font-size: 14px; color: var(--color-ink-subtle); }

/* Installation Guide */
.install-guide {
  text-align: left;
  max-width: 480px;
  width: 100%;
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  margin-top: var(--space-md);
}

.guide-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: var(--space-md);
  text-align: center;
}

.install-step {
  margin-bottom: var(--space-md);
}

.install-step:last-child {
  margin-bottom: 0;
}

.step-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-xs);
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

.step-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink);
}

.step-desc {
  font-size: 13px;
  color: var(--color-ink-subtle);
  margin-bottom: var(--space-sm);
  padding-left: 32px;
}

.code-block {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  background: var(--color-surface-2);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  padding: 10px 12px;
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

.cmd-list {
  margin-left: 32px;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.cmd-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 13px;
}

.cmd-item code {
  font-family: var(--font-mono);
  font-size: 12px;
  background: var(--color-surface-2);
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  color: var(--color-ink);
}

.cmd-desc {
  color: var(--color-ink-subtle);
}

.support-info {
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-hairline);
}

.support-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 12px;
  color: var(--color-ink-subtle);
  background: var(--color-surface-2);
  padding: 6px 12px;
  border-radius: var(--radius-pill);
}

@media (max-width: 768px) {
  .install-guide {
    max-width: 100%;
  }

  .code-block {
    flex-direction: column;
    align-items: flex-start;
  }

  .btn-copy {
    align-self: flex-end;
  }
}

.desktop-only { display: block; }
.mobile-only { display: none; }

@media (max-width: 768px) {
  .desktop-only { display: none !important; }
  .mobile-only { display: flex !important; }
  .page-header { flex-direction: column; }
  .header-actions { width: 100%; }
  .header-actions .btn { flex: 1; justify-content: center; }
  .page-title { font-size: 24px; }
  .lookup-input-group { flex-direction: column; }
  .lookup-input-group .btn { width: 100%; justify-content: center; }
}
</style>
