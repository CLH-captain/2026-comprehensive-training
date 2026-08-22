import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import { http } from '@/api/http'
import SetupView from '@/views/SetupView.vue'

vi.mock('@/api/http', () => ({
  http: { get: vi.fn() },
}))

describe('SetupView', () => {
  it('shows the backend health result', async () => {
    vi.mocked(http.get).mockResolvedValue({
      data: {
        status: 'ok',
        service: 'SZUT Club Activity Agent',
        environment: 'test',
      },
    })

    const wrapper = mount(SetupView)
    await flushPromises()

    expect(wrapper.text()).toContain('后端服务已连接')
    expect(wrapper.text()).toContain('SZUT Club Activity Agent')
  })

  it('explains how to recover when the backend is unavailable', async () => {
    vi.mocked(http.get).mockRejectedValue(new Error('network unavailable'))

    const wrapper = mount(SetupView)
    await flushPromises()

    expect(wrapper.text()).toContain('暂时无法连接后端')
    expect(wrapper.get('button').text()).toContain('重新检查')
  })
})
