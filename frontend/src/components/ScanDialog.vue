<template>
  <Teleport to="body">
    <Transition name="scan-dialog">
      <div v-if="visible" class="scan-dialog-overlay" @click.self="$emit('close')">
        <div class="scan-dialog">
          <!-- Header -->
          <div class="scan-dialog-header">
            <div class="scan-dialog-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="scan-icon">
                <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <h3>网络扫描</h3>
            </div>
            <button class="scan-dialog-close" @click="$emit('close')">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Content -->
          <div class="scan-dialog-content">
            <!-- 扫描模式选择 -->
            <div v-if="!scanning && !scanComplete" class="scan-mode-select">
              <p class="scan-mode-desc">选择扫描方式以发现局域网中的设备</p>
              
              <div class="scan-mode-options">
                <div 
                  class="scan-mode-card" 
                  :class="{ active: scanMode === 'server' }"
                  @click="scanMode = 'server'"
                >
                  <div class="mode-icon server">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <path d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
                    </svg>
                  </div>
                  <div class="mode-info">
                    <h4>服务端扫描</h4>
                    <p>通过服务器 ARP 探测，发现所有活跃设备</p>
                  </div>
                  <div class="mode-badge recommended">推荐</div>
                </div>

                <div 
                  v-if="hasClient"
                  class="scan-mode-card"
                  :class="{ active: scanMode === 'client' }"
                  @click="scanMode = 'client'"
                >
                  <div class="mode-icon client">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <path d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                    </svg>
                  </div>
                  <div class="mode-info">
                    <h4>客户端扫描</h4>
                    <p>通过已连接的客户端代理扫描本地网络</p>
                  </div>
                  <div class="mode-badge online">{{ onlineClients }} 台在线</div>
                </div>

                <div 
                  class="scan-mode-card"
                  :class="{ active: scanMode === 'browser' }"
                  @click="scanMode = 'browser'"
                >
                  <div class="mode-icon browser">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <path d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                    </svg>
                  </div>
                  <div class="mode-info">
                    <h4>浏览器扫描</h4>
                    <p>通过浏览器探测端口，快速发现 Web 设备</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- 扫描进度 -->
            <div v-if="scanning" class="scan-progress">
              <div class="progress-visual">
                <div class="progress-ring">
                  <svg viewBox="0 0 100 100">
                    <circle class="progress-bg" cx="50" cy="50" r="45" />
                    <circle 
                      class="progress-fill" 
                      cx="50" 
                      cy="50" 
                      r="45"
                      :style="{ strokeDashoffset: progressOffset }"
                    />
                  </svg>
                  <div class="progress-percent">{{ progressPercent }}%</div>
                </div>
              </div>
              <div class="progress-info">
                <p class="progress-status">{{ scanStatusText }}</p>
                <p class="progress-detail">{{ scanDetail }}</p>
              </div>
            </div>

            <!-- 扫描结果 -->
            <div v-if="scanComplete && !matching" class="scan-results">
              <div class="results-summary">
                <div class="result-stat">
                  <span class="stat-value">{{ resultCount }}</span>
                  <span class="stat-label">发现设备</span>
                </div>
                <div class="result-stat">
                  <span class="stat-value new">{{ newCount }}</span>
                  <span class="stat-label">新增设备</span>
                </div>
                <div class="result-stat">
                  <span class="stat-value alert">{{ alertCount }}</span>
                  <span class="stat-label">安全告警</span>
                </div>
              </div>
              <p class="results-hint">设备已自动保存到设备列表</p>
            </div>

            <!-- 指纹匹配动画 -->
            <div v-if="matching" class="match-progress">
              <div class="match-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="match-spin">
                  <path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <p class="match-title">正在匹配指纹库...</p>
              <p class="match-detail">已匹配 {{ matchCurrent }}/{{ matchTotal }} 台设备</p>
              <div class="match-bar">
                <div class="match-bar-fill" :style="{ width: matchPercent + '%' }"></div>
              </div>
              <div class="match-list">
                <div v-for="(item, idx) in matchLog" :key="idx" class="match-item" :class="{ 'match-new': item.isNew }">
                  <span class="match-ip">{{ item.ip }}</span>
                  <span class="match-type">{{ item.type }}</span>
                  <span v-if="item.vendor" class="match-vendor">{{ item.vendor }}</span>
                </div>
              </div>
            </div>

            <!-- 错误状态 -->
            <div v-if="scanError" class="scan-error">
              <div class="error-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <p class="error-text">{{ scanError }}</p>
            </div>
          </div>

          <!-- Footer -->
          <div class="scan-dialog-footer">
            <button v-if="!scanning && !scanComplete" class="btn btn-secondary" @click="$emit('close')">
              取消
            </button>
            <button 
              v-if="!scanning && !scanComplete" 
              class="btn btn-primary" 
              :disabled="!scanMode"
              @click="startScan"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="btn-icon">
                <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              开始扫描
            </button>
            <button v-if="scanning" class="btn btn-secondary" @click="cancelScan">
              取消扫描
            </button>
            <button v-if="scanComplete || scanError" class="btn btn-primary" @click="$emit('close')">
              完成
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
export default {
  name: 'ScanDialog',
  props: {
    visible: Boolean,
    hasClient: Boolean,
    onlineClients: Number,
    clients: { type: Array, default: () => [] },
  },
  emits: ['close', 'scan-start', 'scan-complete'],
  data() {
    return {
      scanMode: 'server',
      scanning: false,
      scanComplete: false,
      scanError: '',
      scanProgress: null,
      resultCount: 0,
      newCount: 0,
      alertCount: 0,
      scanId: null,
      matching: false,
      matchCurrent: 0,
      matchTotal: 0,
      matchPercent: 0,
      matchLog: [],
    }
  },
  computed: {
    progressPercent() {
      if (!this.scanProgress) return 0
      return this.scanProgress.progress || 0
    },
    progressOffset() {
      const circumference = 2 * Math.PI * 45
      return circumference - (this.progressPercent / 100) * circumference
    },
    scanStatusText() {
      if (!this.scanProgress) return '准备中...'
      const status = this.scanProgress.status
      if (status === 'detecting_ip') return '检测网络环境'
      if (status === 'scanning') return '扫描中'
      if (status === 'complete') return '扫描完成'
      if (status === 'error') return '扫描失败'
      return '处理中...'
    },
    scanDetail() {
      if (!this.scanProgress) return ''
      return this.scanProgress.message || ''
    },
  },
  watch: {
    visible(val) {
      if (val) {
        this.resetState()
      }
    }
  },
  methods: {
    resetState() {
      this.scanning = false
      this.scanComplete = false
      this.scanError = ''
      this.scanProgress = null
      this.resultCount = 0
      this.newCount = 0
      this.alertCount = 0
      this.scanId = null
    },
    async startScan() {
      this.scanning = true
      this.scanError = ''
      this.$emit('scan-start')
      
      try {
        if (this.scanMode === 'server') {
          await this.scanServer()
        } else if (this.scanMode === 'client') {
          await this.scanClient()
        } else if (this.scanMode === 'browser') {
          await this.scanBrowser()
        }
      } catch (e) {
        this.scanError = e.message || '扫描失败'
      }
    },
    async scanServer() {
      const api = (await import('@/api')).default
      
      // 模拟进度更新
      this.scanProgress = { status: 'scanning', progress: 10, message: '正在执行 ARP 探测...' }
      const progressTimer = setInterval(() => {
        if (this.scanProgress && this.scanProgress.progress < 90) {
          this.scanProgress = {
            ...this.scanProgress,
            progress: this.scanProgress.progress + 5,
            message: this.scanProgress.progress < 50 ? '正在填充 ARP 表...' : '正在读取设备列表...'
          }
        }
      }, 500)
      
      try {
        const res = await api.post('/devices/scan')
        clearInterval(progressTimer)
        this.scanProgress = { status: 'scanning', progress: 95, message: '正在处理结果...' }
        this.resultCount = res.data.device_count || 0
        this.newCount = res.data.new_device_count || 0
        this.alertCount = res.data.alerts_created || 0
        this.scanProgress = { status: 'complete', progress: 100, message: '扫描完成' }
        this.scanComplete = true
        await this.startMatching()
      } catch (e) {
        clearInterval(progressTimer)
        throw new Error(e.response?.data?.detail || '服务端扫描失败')
      }
    },
    async scanClient() {
      const api = (await import('@/api')).default
      
      // 获取在线客户端的 client_id
      const onlineClient = this.clients.find(c => c.is_online)
      if (!onlineClient) {
        throw new Error('没有在线的客户端')
      }
      
      this.scanProgress = { status: 'scanning', progress: 10, message: `正在向 ${onlineClient.hostname || onlineClient.client_id} 发送扫描指令...` }
      
      try {
        const res = await api.post('/devices/scan-client', { client_id: onlineClient.client_id })
        this.scanId = res.data.scan_id
        
        // Poll for completion
        await this.pollClientScan()
        this.scanComplete = true
        await this.startMatching()
      } catch (e) {
        throw new Error(e.response?.data?.detail || '客户端扫描失败')
      }
    },
    async pollClientScan() {
      const api = (await import('@/api')).default
      const maxPolls = 60
      
      for (let i = 0; i < maxPolls; i++) {
        await new Promise(r => setTimeout(r, 2000))
        
        try {
          const res = await api.get(`/devices/scan-client/${this.scanId}`)
          const status = res.data
          
          this.scanProgress = {
            status: 'scanning',
            progress: Math.min(90, 20 + Math.round((i / maxPolls) * 70)),
            message: `已发现 ${status.device_count || 0} 台设备...`
          }
          
          if (status.status === 'complete') {
            this.scanProgress = { status: 'complete', progress: 100, message: '扫描完成' }
            this.resultCount = status.device_count || 0
            this.newCount = status.new_device_count || 0
            return
          } else if (status.status === 'error') {
            throw new Error(status.message || '扫描失败')
          }
        } catch (e) {
          if (e.response?.status === 404) continue
          throw e
        }
      }
      
      throw new Error('扫描超时')
    },
    async scanBrowser() {
      const { BrowserScanner } = await import('@/utils/browser-scanner.js')
      const scanner = new BrowserScanner()
      
      const devices = []
      
      await scanner.scan(
        (device) => {
          devices.push(device)
          this.scanProgress = {
            status: 'scanning',
            progress: Math.min(90, devices.length * 2),
            message: `已发现 ${devices.length} 台设备...`
          }
        },
        (progress) => {
          this.scanProgress = progress
        }
      )
      
      if (devices.length > 0) {
        this.resultCount = devices.length
        this.scanComplete = true
        await this.startMatching()
      } else {
        throw new Error('浏览器扫描未发现设备，请尝试其他扫描方式')
      }
    },
    async startMatching() {
      const api = (await import('@/api')).default
      try {
        const res = await api.get('/devices/')
        const devices = res.data
        this.matchTotal = devices.length
        this.matching = true
        this.matchLog = []
        this.matchCurrent = 0

        for (let i = 0; i < devices.length; i++) {
          const d = devices[i]
          this.matchCurrent = i + 1
          this.matchPercent = Math.round((this.matchCurrent / this.matchTotal) * 100)
          
          const vendor = d.vendor || ''
          const deviceType = d.device_type || 'unknown'
          
          this.matchLog.unshift({
            ip: d.ip_address || '',
            type: deviceType,
            vendor: vendor,
            isNew: d.mac_address && d.mac_address.startsWith('02:'),
          })
          
          // 保持最多显示 5 条
          if (this.matchLog.length > 5) {
            this.matchLog.pop()
          }
          
          await new Promise(r => setTimeout(r, 80))
        }

        await new Promise(r => setTimeout(r, 500))
        this.matching = false
        this.$emit('scan-complete')
      } catch (e) {
        this.matching = false
        this.$emit('scan-complete')
      }
    },
    cancelScan() {
      this.scanning = false
      this.scanError = '扫描已取消'
    }
  }
}
</script>

<style scoped>
.scan-dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.scan-dialog {
  width: 480px;
  max-width: 90vw;
  max-height: 85vh;
  background: var(--color-surface-1, #0f1011);
  border: 1px solid var(--color-hairline, rgba(255, 255, 255, 0.08));
  border-radius: var(--radius-xl, 16px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.scan-dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-hairline, rgba(255, 255, 255, 0.08));
}

.scan-dialog-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.scan-dialog-title h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-ink, #f7f8f8);
}

.scan-icon {
  width: 20px;
  height: 20px;
  color: var(--color-primary, #5e6ad2);
}

.scan-dialog-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm, 6px);
  color: var(--color-ink-subtle, #8a8f98);
  cursor: pointer;
  transition: all 150ms ease;
}

.scan-dialog-close:hover {
  background: var(--color-surface-2, #141516);
  color: var(--color-ink, #f7f8f8);
}

.scan-dialog-close svg {
  width: 16px;
  height: 16px;
}

.scan-dialog-content {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.scan-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--color-hairline, rgba(255, 255, 255, 0.08));
}

/* Mode Selection */
.scan-mode-desc {
  margin: 0 0 20px;
  color: var(--color-ink-muted, #d0d6e0);
  font-size: 14px;
}

.scan-mode-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.scan-mode-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--color-surface-2, #141516);
  border: 1px solid var(--color-hairline, rgba(255, 255, 255, 0.08));
  border-radius: var(--radius-lg, 12px);
  cursor: pointer;
  transition: all 200ms ease;
}

.scan-mode-card:hover {
  border-color: var(--color-hairline-strong, rgba(255, 255, 255, 0.12));
}

.scan-mode-card.active {
  border-color: var(--color-primary, #5e6ad2);
  background: rgba(94, 106, 210, 0.08);
}

.mode-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md, 8px);
  flex-shrink: 0;
}

.mode-icon svg {
  width: 24px;
  height: 24px;
}

.mode-icon.server {
  background: rgba(94, 106, 210, 0.15);
  color: var(--color-primary, #5e6ad2);
}

.mode-icon.client {
  background: rgba(39, 166, 68, 0.15);
  color: var(--color-success, #27a644);
}

.mode-icon.browser {
  background: rgba(245, 158, 11, 0.15);
  color: var(--color-warning, #f59e0b);
}

.mode-info {
  flex: 1;
  min-width: 0;
}

.mode-info h4 {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-ink, #f7f8f8);
}

.mode-info p {
  margin: 0;
  font-size: 12px;
  color: var(--color-ink-subtle, #8a8f98);
}

.mode-badge {
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 500;
  border-radius: var(--radius-sm, 6px);
  flex-shrink: 0;
}

.mode-badge.recommended {
  background: rgba(94, 106, 210, 0.15);
  color: var(--color-primary, #5e6ad2);
}

.mode-badge.online {
  background: rgba(39, 166, 68, 0.15);
  color: var(--color-success, #27a644);
}

/* Progress */
.scan-progress {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
}

.progress-visual {
  margin-bottom: 24px;
}

.progress-ring {
  position: relative;
  width: 120px;
  height: 120px;
}

.progress-ring svg {
  transform: rotate(-90deg);
  width: 100%;
  height: 100%;
}

.progress-bg {
  fill: none;
  stroke: var(--color-surface-2, #141516);
  stroke-width: 6;
}

.progress-fill {
  fill: none;
  stroke: var(--color-primary, #5e6ad2);
  stroke-width: 6;
  stroke-linecap: round;
  stroke-dasharray: 283;
  transition: stroke-dashoffset 300ms ease;
}

.progress-percent {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 600;
  color: var(--color-ink, #f7f8f8);
}

.progress-info {
  text-align: center;
}

.progress-status {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 500;
  color: var(--color-ink, #f7f8f8);
}

.progress-detail {
  margin: 0;
  font-size: 13px;
  color: var(--color-ink-subtle, #8a8f98);
}

/* Results */
.scan-results {
  text-align: center;
  padding: 20px 0;
}

.results-summary {
  display: flex;
  justify-content: center;
  gap: 40px;
  margin-bottom: 16px;
}

.result-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: var(--color-ink, #f7f8f8);
  line-height: 1;
}

.stat-value.new {
  color: var(--color-primary, #5e6ad2);
}

.stat-value.alert {
  color: var(--color-warning, #f59e0b);
}

.stat-label {
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-ink-subtle, #8a8f98);
}

.results-hint {
  margin: 0;
  font-size: 13px;
  color: var(--color-ink-subtle, #8a8f98);
}

/* Error */
.scan-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
}

.error-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(239, 68, 68, 0.15);
  border-radius: 50%;
  margin-bottom: 16px;
}

.error-icon svg {
  width: 24px;
  height: 24px;
  color: var(--color-danger, #ef4444);
}

.error-text {
  margin: 0;
  font-size: 14px;
  color: var(--color-ink-muted, #d0d6e0);
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 500;
  border-radius: var(--radius-md, 8px);
  cursor: pointer;
  transition: all 150ms ease;
  border: none;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--color-primary, #5e6ad2);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-hover, #828fff);
}

.btn-secondary {
  background: var(--color-surface-2, #141516);
  color: var(--color-ink-muted, #d0d6e0);
  border: 1px solid var(--color-hairline, rgba(255, 255, 255, 0.08));
}

.btn-secondary:hover {
  background: var(--color-surface-3, #18191a);
  border-color: var(--color-hairline-strong, rgba(255, 255, 255, 0.12));
}

.btn-icon {
  width: 16px;
  height: 16px;
}

/* Match Progress */
.match-progress {
  text-align: center;
  padding: 10px 0;
}

.match-icon {
  margin-bottom: 16px;
}

.match-spin {
  width: 48px;
  height: 48px;
  color: var(--color-primary, #5e6ad2);
  animation: spin 2s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.match-title {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 500;
  color: var(--color-ink, #f7f8f8);
}

.match-detail {
  margin: 0 0 16px;
  font-size: 13px;
  color: var(--color-ink-subtle, #8a8f98);
}

.match-bar {
  width: 100%;
  height: 4px;
  background: var(--color-surface-2, #141516);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 16px;
}

.match-bar-fill {
  height: 100%;
  background: var(--color-primary, #5e6ad2);
  border-radius: 2px;
  transition: width 100ms ease;
}

.match-list {
  max-height: 120px;
  overflow-y: auto;
}

.match-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 12px;
  font-size: 12px;
  border-radius: 4px;
  animation: fadeIn 200ms ease;
}

.match-item.match-new {
  background: rgba(94, 106, 210, 0.08);
}

.match-ip {
  font-family: var(--font-mono, monospace);
  color: var(--color-ink-muted, #d0d6e0);
  min-width: 100px;
}

.match-type {
  padding: 2px 8px;
  background: var(--color-surface-2, #141516);
  border-radius: 4px;
  color: var(--color-ink-subtle, #8a8f98);
}

.match-vendor {
  color: var(--color-ink-subtle, #8a8f98);
  flex: 1;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Transitions */
.scan-dialog-enter-active,
.scan-dialog-leave-active {
  transition: opacity 200ms ease;
}

.scan-dialog-enter-active .scan-dialog,
.scan-dialog-leave-active .scan-dialog {
  transition: transform 200ms ease, opacity 200ms ease;
}

.scan-dialog-enter-from,
.scan-dialog-leave-to {
  opacity: 0;
}

.scan-dialog-enter-from .scan-dialog,
.scan-dialog-leave-to .scan-dialog {
  transform: scale(0.95);
  opacity: 0;
}
</style>
