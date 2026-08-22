import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { http } from '@/api/http'
import type { CurrentUser, LoginResponse } from '@/types/auth'

export const TOKEN_KEY = 'szut_access_token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) ?? '')
  const user = ref<CurrentUser | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => Boolean(token.value))
  const isAdmin = computed(() => user.value?.role === 'admin')
  const canManageClubs = computed(() =>
    user.value?.role === 'admin' || user.value?.role === 'club_manager',
  )

  function saveToken(value: string): void {
    token.value = value
    localStorage.setItem(TOKEN_KEY, value)
  }

  function clear(): void {
    token.value = ''
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
  }

  async function login(username: string, password: string): Promise<void> {
    loading.value = true
    try {
      const response = await http.post<LoginResponse>('/auth/login', { username, password })
      saveToken(response.data.access_token)
      user.value = response.data.user
    } finally {
      loading.value = false
    }
  }

  async function restore(): Promise<boolean> {
    if (!token.value) return false
    try {
      user.value = (await http.get<CurrentUser>('/auth/me')).data
      return true
    } catch {
      clear()
      return false
    }
  }

  async function logout(): Promise<void> {
    try {
      if (token.value) await http.post('/auth/logout')
    } finally {
      clear()
    }
  }

  return { token, user, loading, isAuthenticated, isAdmin, canManageClubs, login, restore, logout, clear }
})
