import { createRouter, createWebHistory } from 'vue-router'

import ClubManagementView from '@/views/ClubManagementView.vue'
import DashboardView from '@/views/DashboardView.vue'
import StudentManagementView from '@/views/StudentManagementView.vue'

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: DashboardView,
    },
    {
      path: '/students',
      name: 'students',
      component: StudentManagementView,
    },
    {
      path: '/clubs',
      name: 'clubs',
      component: ClubManagementView,
    },
  ],
})
