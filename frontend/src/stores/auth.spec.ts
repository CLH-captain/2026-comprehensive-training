import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { http } from '@/api/http'
import { TOKEN_KEY, useAuthStore } from '@/stores/auth'

vi.mock('@/api/http', () => ({
  http: { post: vi.fn(), get: vi.fn() },
}))

describe('auth store', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('stores token and current user after login', async () => {
    vi.mocked(http.post).mockResolvedValueOnce({
      data: {
        access_token: 'test-token',
        token_type: 'bearer',
        expires_at: '2026-08-22T18:00:00Z',
        user: { id: 1, username: 'admin', role: 'admin', student_id: null },
      },
    })
    const auth = useAuthStore()
    await auth.login('admin', 'password')
    expect(auth.isAuthenticated).toBe(true)
    expect(auth.isAdmin).toBe(true)
    expect(localStorage.getItem(TOKEN_KEY)).toBe('test-token')
  })

  it('clears local session after logout', async () => {
    localStorage.setItem(TOKEN_KEY, 'test-token')
    vi.mocked(http.post).mockResolvedValueOnce({ data: null })
    const auth = useAuthStore()
    await auth.logout()
    expect(auth.isAuthenticated).toBe(false)
    expect(localStorage.getItem(TOKEN_KEY)).toBeNull()
  })
})
