<template>
  <div class="app">
    <!-- Desktop Sidebar -->
    <aside v-if="!isMobile" class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-logo">
          <svg viewBox="0 0 1024 1024" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M593.408 64.341333l147.114667 84.906667a32 32 0 0 1-32 55.466667l-147.114667-84.992a96 96 0 0 0-96 0L241.493333 249.002667a127.402667 127.402667 0 0 1 13.226667 88.917333l103.765333 51.797333a191.744 191.744 0 0 1 155.050667-78.592c63.914667 0 120.490667 31.232 155.392 79.274667l103.68-51.285333a127.744 127.744 0 0 1-2.56-15.701334l-0.512-12.288a128 128 0 1 1 163.84 122.88l0.085333 219.221334c0 57.173333-30.464 109.994667-79.957333 138.496l-115.626667 66.816a32 32 0 0 1-32-55.466667l115.626667-66.730667c29.696-17.152 47.957333-48.810667 47.957333-83.114666V436.053333a127.914667 127.914667 0 0 1-67.584-39.850666l-104.448 51.712a192 192 0 0 1-130.56 239.701333v83.114667a128 128 0 1 1-178.005333 145.493333L173.482667 791.722667a160 160 0 0 1-80.042667-138.496V525.824a32 32 0 1 1 64 0v127.402667c0 34.304 18.346667 65.962667 48.042667 83.114666l187.221333 108.202667c14.08-39.936 47.36-70.826667 88.746667-81.408v-70.656A192 192 0 0 1 329.728 447.146667l-103.765333-51.968c-20.992 23.978667-50.688 40.106667-84.224 43.349333l-12.288 0.597333a128 128 0 1 1 66.218666-237.568L433.408 64.341333a160 160 0 0 1 160 0z" fill="var(--color-primary)"/>
          </svg>
        </div>
        <span class="brand-name">NetGuard</span>
        <router-link to="/alerts" class="brand-alert" :class="{ 'has-alerts': alertCount > 0 }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          <span v-if="alertCount > 0" class="brand-alert-badge">{{ alertCount > 99 ? '99+' : alertCount }}</span>
        </router-link>
      </div>
      <nav class="sidebar-nav">
        <router-link to="/" class="nav-item" :class="{ active: $route.path === '/' }">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          <span>{{ t('nav.dashboard') }}</span>
        </router-link>
        <router-link to="/devices" class="nav-item" :class="{ active: $route.path === '/devices' }">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
          </svg>
          <span>{{ t('nav.devices') }}</span>
        </router-link>
        <router-link to="/libraries" class="nav-item" :class="{ active: $route.path === '/libraries' }">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span>{{ t('nav.libraries') }}</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <div class="sidebar-status">
          <span class="status-dot"></span>
          <span class="status-text">{{ t('nav.systemOnline') }}</span>
        </div>
        <div class="sidebar-bottom-row">
          <div class="lang-switcher">
            <button class="lang-btn" :class="{ active: locale === 'zh-CN' }" @click="switchLang('zh-CN')">中文</button>
            <button class="lang-btn" :class="{ active: locale === 'en' }" @click="switchLang('en')">EN</button>
          </div>
          <button class="settings-btn" @click="showSettings = true" title="设置">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
          </button>
        </div>
      </div>
    </aside>

    <!-- Settings Panel -->
    <SettingsPanel :visible="showSettings" @close="showSettings = false" />

    <!-- Mobile Topbar -->
    <header v-if="isMobile" class="topbar">
      <div class="topbar-brand">
        <div class="brand-logo">
          <svg viewBox="0 0 1024 1024" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M593.408 64.341333l147.114667 84.906667a32 32 0 0 1-32 55.466667l-147.114667-84.992a96 96 0 0 0-96 0L241.493333 249.002667a127.402667 127.402667 0 0 1 13.226667 88.917333l103.765333 51.797333a191.744 191.744 0 0 1 155.050667-78.592c63.914667 0 120.490667 31.232 155.392 79.274667l103.68-51.285333a127.744 127.744 0 0 1-2.56-15.701334l-0.512-12.288a128 128 0 1 1 163.84 122.88l0.085333 219.221334c0 57.173333-30.464 109.994667-79.957333 138.496l-115.626667 66.816a32 32 0 0 1-32-55.466667l115.626667-66.730667c29.696-17.152 47.957333-48.810667 47.957333-83.114666V436.053333a127.914667 127.914667 0 0 1-67.584-39.850666l-104.448 51.712a192 192 0 0 1-130.56 239.701333v83.114667a128 128 0 1 1-178.005333 145.493333L173.482667 791.722667a160 160 0 0 1-80.042667-138.496V525.824a32 32 0 1 1 64 0v127.402667c0 34.304 18.346667 65.962667 48.042667 83.114666l187.221333 108.202667c14.08-39.936 47.36-70.826667 88.746667-81.408v-70.656A192 192 0 0 1 329.728 447.146667l-103.765333-51.968c-20.992 23.978667-50.688 40.106667-84.224 43.349333l-12.288 0.597333a128 128 0 1 1 66.218666-237.568L433.408 64.341333a160 160 0 0 1 160 0z" fill="var(--color-primary)"/>
          </svg>
        </div>
        <span class="brand-name">NetGuard</span>
        <router-link to="/alerts" class="topbar-alert" :class="{ 'has-alerts': alertCount > 0 }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          <span v-if="alertCount > 0" class="topbar-alert-badge">{{ alertCount > 99 ? '99+' : alertCount }}</span>
        </router-link>
      </div>
      <div class="topbar-actions">
        <button class="topbar-btn" @click="toggleThemeMode">
          <svg v-if="effectiveTheme === 'dark'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="12" cy="12" r="5"/><path d="M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72l1.42 1.42M1 12h2m18 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/>
          </svg>
        </button>
        <div class="lang-switcher">
          <button class="lang-btn" :class="{ active: locale === 'zh-CN' }" @click="switchLang('zh-CN')">中</button>
          <button class="lang-btn" :class="{ active: locale === 'en' }" @click="switchLang('en')">EN</button>
        </div>
      </div>
    </header>

    <!-- Global Notification -->
    <Transition name="slide">
      <div v-if="showNotification" class="global-notification" :class="'notification--' + notificationSeverity" @click="goToAlerts">
        <div class="notification-content">
          <svg class="notification-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          <div class="notification-text">
            <span class="notification-title">{{ notificationTitle }}</span>
            <span class="notification-message">{{ notificationMessage }}</span>
          </div>
        </div>
        <button class="notification-close" @click.stop="showNotification = false">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </Transition>

    <!-- Main Content -->
    <main class="main" :class="{ 'main--mobile': isMobile }">
      <router-view />
    </main>

    <!-- Mobile Bottom Nav -->
    <nav v-if="isMobile" class="bottom-nav">
      <router-link to="/" class="bottom-nav-item" :class="{ active: $route.path === '/' }">
        <svg class="bottom-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
        <span>{{ t('nav.dashboard') }}</span>
      </router-link>
      <router-link to="/devices" class="bottom-nav-item" :class="{ active: $route.path === '/devices' }">
        <svg class="bottom-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
        </svg>
        <span>{{ t('nav.devices') }}</span>
      </router-link>
      <router-link to="/libraries" class="bottom-nav-item" :class="{ active: $route.path === '/libraries' }">
        <svg class="bottom-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <span>{{ t('nav.libraries') }}</span>
      </router-link>
    </nav>
  </div>
</template>

<script>
import { useI18n } from 'vue-i18n'
import api from '@/api'
import SettingsPanel from '@/components/SettingsPanel.vue'
import { useTheme } from '@/composables/useTheme'

export default {
  name: 'App',
  components: { SettingsPanel },
  setup() {
    const { t, locale } = useI18n()
    const { mode, toggleTheme, effectiveTheme } = useTheme()
    return { t, locale, themeMode: mode, toggleThemeMode: toggleTheme, effectiveTheme }
  },
  data() {
    return {
      isMobile: false,
      alertCount: 0,
      showNotification: false,
      showSettings: false,
      notificationTitle: '',
      notificationMessage: '',
      notificationSeverity: 'warning',
      lastAlertId: 0,
      pollTimer: null
    }
  },
  mounted() {
    this.checkMobile()
    window.addEventListener('resize', this.checkMobile)
    this.loadAlertCount()
    this.pollTimer = setInterval(() => {
      this.loadAlertCount()
      this.checkNewAlerts()
    }, 10000)
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.checkMobile)
    if (this.pollTimer) clearInterval(this.pollTimer)
  },
  methods: {
    checkMobile() {
      this.isMobile = window.innerWidth < 768
    },
    switchLang(lang) {
      this.locale = lang
      localStorage.setItem('netguard-locale', lang)
    },
    goToAlerts() {
      this.showNotification = false
      this.$router.push('/alerts')
    },
    async loadAlertCount() {
      try {
        const res = await api.get('/alerts/')
        if (Array.isArray(res.data)) {
          this.alertCount = res.data.filter(a => !a.acknowledged).length
          if (res.data.length > 0 && this.lastAlertId === 0) {
            this.lastAlertId = Math.max(...res.data.map(a => a.id))
          }
        }
      } catch (e) {
        // ignore
      }
    },
    async checkNewAlerts() {
      try {
        const res = await api.get('/alerts/', { params: { acknowledged: false } })
        if (!Array.isArray(res.data)) return
        const newAlerts = res.data.filter(a => a.id > this.lastAlertId)
        if (newAlerts.length > 0) {
          const criticalAlert = newAlerts.find(a => a.severity === 'CRITICAL') || newAlerts[0]
          this.lastAlertId = Math.max(...newAlerts.map(a => a.id))
          this.notificationSeverity = criticalAlert.severity === 'CRITICAL' ? 'critical' : 'warning'
          this.notificationTitle = this.t('notification.newAlert')
          this.notificationMessage = criticalAlert.message
          this.showNotification = true
          setTimeout(() => { this.showNotification = false }, 8000)
        }
      } catch (e) {
        // ignore
      }
    }
  }
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body {
  height: 100%;
  background: var(--color-canvas);
  color: var(--color-ink);
  font-family: var(--font-body);
  font-size: 14px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app {
  display: flex;
  min-height: 100vh;
  min-height: 100dvh;
}

/* Sidebar */
.sidebar {
  width: 240px;
  background: var(--color-surface-1);
  border-right: 1px solid var(--color-hairline);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  z-index: 100;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-lg);
  border-bottom: 1px solid var(--color-hairline);
}

.brand-logo {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
}

.brand-logo svg {
  width: 100%;
  height: 100%;
}

.brand-name {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.3px;
  color: var(--color-ink);
}

.brand-alert {
  margin-left: auto;
  position: relative;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  color: var(--color-ink-subtle);
  text-decoration: none;
  transition: all var(--transition-fast);
}

.brand-alert:hover {
  background: var(--color-surface-2);
  color: var(--color-ink);
}

.brand-alert.has-alerts {
  color: var(--color-warning);
}

.brand-alert svg {
  width: 18px;
  height: 18px;
}

.brand-alert-badge {
  position: absolute;
  top: -2px;
  right: -4px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  background: var(--color-danger);
  color: white;
  font-size: 10px;
  font-weight: 600;
  border-radius: var(--radius-pill);
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.sidebar-nav {
  flex: 1;
  padding: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-xxs);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 10px 12px;
  border-radius: var(--radius-md);
  color: var(--color-ink-muted);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all var(--transition-fast);
  position: relative;
}

.nav-item:hover {
  background: var(--color-surface-2);
  color: var(--color-ink);
}

.nav-item.active {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.nav-item.active .nav-icon {
  opacity: 1;
}

.nav-icon {
  width: 18px;
  height: 18px;
  opacity: 0.7;
}

.sidebar-footer {
  padding: var(--space-md) var(--space-lg);
  border-top: 1px solid var(--color-hairline);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.sidebar-bottom-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.settings-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-ink-subtle);
  cursor: pointer;
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.settings-btn:hover {
  background: var(--color-surface-2);
  border-color: var(--color-hairline-strong);
  color: var(--color-ink);
}

.settings-btn svg {
  width: 16px;
  height: 16px;
}

.lang-switcher {
  display: flex;
  gap: 2px;
}

.lang-switcher {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
}

.lang-btn {
  padding: 4px 8px;
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-ink-subtle);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.lang-btn:hover {
  border-color: var(--color-hairline-strong);
  color: var(--color-ink);
}

.lang-btn.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-on-primary);
}

.sidebar-status {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.status-dot {
  width: 8px;
  height: 8px;
  background: var(--color-success);
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  font-size: 12px;
  color: var(--color-ink-subtle);
}

/* Topbar */
.topbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 56px;
  background: var(--color-surface-1);
  border-bottom: 1px solid var(--color-hairline);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-sm);
  z-index: 100;
  gap: var(--space-xs);
  overflow: hidden;
}

.topbar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-shrink: 0;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  flex-shrink: 0;
}

.topbar-btn {
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

.topbar-btn:hover {
  background: var(--color-surface-2);
  color: var(--color-ink);
}

.topbar-btn svg {
  width: 18px;
  height: 18px;
}

.topbar-alert {
  margin-left: var(--space-xs);
  position: relative;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  color: var(--color-ink-subtle);
  text-decoration: none;
  transition: all var(--transition-fast);
}

.topbar-alert:hover {
  background: var(--color-surface-2);
  color: var(--color-ink);
}

.topbar-alert.has-alerts {
  color: var(--color-warning);
}

.topbar-alert svg {
  width: 18px;
  height: 18px;
}

.topbar-alert-badge {
  position: absolute;
  top: -2px;
  right: -4px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  background: var(--color-danger);
  color: white;
  font-size: 10px;
  font-weight: 600;
  border-radius: var(--radius-pill);
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.topbar .lang-switcher {
  gap: 2px;
  flex-shrink: 0;
}

.topbar .lang-btn {
  padding: 4px 6px;
  font-size: 11px;
  white-space: nowrap;
}

/* Global Notification */
.global-notification {
  position: fixed;
  top: 16px;
  right: 16px;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-lg);
  border-radius: var(--radius-lg);
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
  box-shadow: var(--shadow-lg);
  max-width: 400px;
  cursor: pointer;
  transition: all var(--transition-base);
}

.global-notification:hover {
  border-color: var(--color-hairline-strong);
}

.notification--warning {
  border-left: 3px solid var(--color-warning);
}

.notification--critical {
  border-left: 3px solid var(--color-danger);
}

.notification-content {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  flex: 1;
  min-width: 0;
}

.notification-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  margin-top: 1px;
}

.notification--warning .notification-icon {
  color: var(--color-warning);
}

.notification--critical .notification-icon {
  color: var(--color-danger);
}

.notification-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.notification-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-ink);
}

.notification-message {
  font-size: 13px;
  color: var(--color-ink-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notification-close {
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

.notification-close:hover {
  background: var(--color-surface-3);
  color: var(--color-ink);
}

.notification-close svg {
  width: 14px;
  height: 14px;
}

.slide-enter-active, .slide-leave-active {
  transition: all var(--transition-base);
}

.slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.slide-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

/* Main */
.main {
  flex: 1;
  padding: var(--space-xl);
  margin-left: 240px;
}

.main--mobile {
  margin-left: 0;
  padding: calc(56px + var(--space-md)) var(--space-md) calc(64px + var(--space-md));
  max-width: 100%;
}

/* Bottom Nav */
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 64px;
  background: var(--color-surface-1);
  border-top: 1px solid var(--color-hairline);
  display: flex;
  justify-content: space-around;
  align-items: center;
  z-index: 100;
  padding-bottom: env(safe-area-inset-bottom);
}

.bottom-nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  color: var(--color-ink-subtle);
  text-decoration: none;
  font-size: 10px;
  font-weight: 500;
  transition: all var(--transition-fast);
  position: relative;
  min-width: 64px;
}

.bottom-nav-item.active {
  color: var(--color-primary);
}

.bottom-nav-icon {
  width: 22px;
  height: 22px;
}

/* Responsive */
@media (max-width: 768px) {
  .sidebar {
    display: none;
  }
  .main {
    margin-left: 0;
  }
  .global-notification {
    top: 64px;
    left: 16px;
    right: 16px;
    max-width: none;
  }
}

@media (min-width: 769px) {
  .topbar,
  .bottom-nav {
    display: none;
  }
}
</style>
