import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Devices from '../views/Devices.vue'
import Alerts from '../views/Alerts.vue'
import Libraries from '../views/Libraries.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/devices', component: Devices },
  { path: '/alerts', component: Alerts },
  { path: '/libraries', component: Libraries }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
