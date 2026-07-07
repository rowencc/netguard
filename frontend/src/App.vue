<template>
  <div class="app">
    <!-- Desktop Sidebar -->
    <aside v-if="!isMobile" class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-logo">
          <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="2" y="2" width="28" height="28" rx="6" fill="#5e6ad2"/>
            <path d="M16 6L8 10v6c0 5.52 3.42 10.68 8 12 4.58-1.32 8-6.48 8-12v-6l-8-4z" fill="none" stroke="white" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="M12 15l3 3 5-5" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
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
        <div class="lang-switcher">
          <button class="lang-btn" :class="{ active: locale === 'zh-CN' }" @click="switchLang('zh-CN')">中文</button>
          <button class="lang-btn" :class="{ active: locale === 'en' }" @click="switchLang('en')">EN</button>
        </div>
        <div class="sidebar-status">
          <span class="status-dot"></span>
          <span class="status-text">{{ t('nav.systemOnline') }}</span>
        </div>
      </div>
    </aside>

    <!-- Mobile Topbar -->
    <header v-if="isMobile" class="topbar">
      <div class="topbar-brand">
        <div class="brand-logo">
          <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="2" y="2" width="28" height="28" rx="6" fill="#5e6ad2"/>
            <path d="M16 6L8 10v6c0 5.52 3.42 10.68 8 12 4.58-1.32 8-6.48 8-12v-6l-8-4z" fill="none" stroke="white" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="M12 15l3 3 5-5" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
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
      <div class="lang-switcher">
        <button class="lang-btn" :class="{ active: locale === 'zh-CN' }" @click="switchLang('zh-CN')">中文</button>
        <button class="lang-btn" :class="{ active: locale === 'en' }" @click="switchLang('en')">EN</button>
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

export default {
  name: 'App',
  setup() {
    const { t, locale } = useI18n()
    return { t, locale }
  },
  data() {
    return {
      isMobile: false,
      alertCount: 0,
      showNotification: false,
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
  width: 28px;
  height: 28px;
  flex-shrink: 0;
}

.brand-logo svg {
  width: 100%;
  height: 100%;
}

.brand-name {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -0.5px;
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

.lang-switcher {
  display: flex;
  gap: var(--space-xxs);
}

.lang-btn {
  flex: 1;
  padding: 4px 8px;
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-ink-subtle);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
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
  padding: 0 var(--space-md);
  z-index: 100;
}

.topbar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
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
  gap: var(--space-xxs);
}

.topbar .lang-btn {
  padding: 3px 6px;
  font-size: 11px;
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
