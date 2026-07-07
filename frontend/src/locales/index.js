import { createI18n } from 'vue-i18n'
import en from './en.js'
import zhCN from './zh-CN.js'

const savedLocale = localStorage.getItem('netguard-locale') || 'zh-CN'

const i18n = createI18n({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'en',
  messages: {
    en,
    'zh-CN': zhCN
  }
})

export default i18n
