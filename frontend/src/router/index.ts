import { createRouter, createWebHistory } from 'vue-router'

import ActivityManagementView from '@/views/ActivityManagementView.vue'
import AgentView from '@/views/AgentView.vue'
import AnalyticsView from '@/views/AnalyticsView.vue'
import ClubManagementView from '@/views/ClubManagementView.vue'
import DashboardView from '@/views/DashboardView.vue'
import LoginView from '@/views/LoginView.vue'
import ParticipationManagementView from '@/views/ParticipationManagementView.vue'
import StudentManagementView from '@/views/StudentManagementView.vue'
import { TOKEN_KEY } from '@/stores/auth'

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/login', name: 'login', component: LoginView, meta: { public: true } },
    { path: '/', name: 'dashboard', component: DashboardView },
    { path: '/students', name: 'students', component: StudentManagementView },
    { path: '/clubs', name: 'clubs', component: ClubManagementView },
    { path: '/activities', name: 'activities', component: ActivityManagementView },
    { path: '/participation', name: 'participation', component: ParticipationManagementView },
    { path: '/analytics', name: 'analytics', component: AnalyticsView },
    { path: '/agent', name: 'agent', component: AgentView },
  ],
})

router.beforeEach((to) => {
  const authenticated = Boolean(localStorage.getItem(TOKEN_KEY))
  if (!to.meta.public && !authenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && authenticated) return { name: 'dashboard' }
  return true
})