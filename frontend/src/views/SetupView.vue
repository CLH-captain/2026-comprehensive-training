<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { http } from '@/api/http'
import type { HealthResponse } from '@/types/health'

type ConnectionState = 'loading' | 'connected' | 'error'

const state = ref<ConnectionState>('loading')
const health = ref<HealthResponse | null>(null)

const statusLabel = computed(() => {
  if (state.value === 'connected') return '后端服务已连接'
  if (state.value === 'error') return '暂时无法连接后端'
  return '正在检查服务'
})

async function checkBackend(): Promise<void> {
  state.value = 'loading'
  health.value = null

  try {
    const response = await http.get<HealthResponse>('/health')
    health.value = response.data
    state.value = 'connected'
  } catch {
    state.value = 'error'
  }
}

onMounted(checkBackend)
</script>

<template>
  <main class="setup-page">
    <section class="campus-panel" aria-labelledby="product-title">
      <div class="brand-mark" aria-hidden="true">SZUT</div>
      <div class="campus-copy">
        <p class="eyebrow">苏州工学院 · 校园数据工作台</p>
        <h1 id="product-title">让每一次校园参与<br />都有据可循</h1>
        <p class="intro">
          连接社团、活动与学生参与记录，建立可信的统计分析与智能问答基础。
        </p>
      </div>

      <div class="campus-line" aria-label="东湖校区与东南校区">
        <span class="campus-node campus-node--start">东湖校区</span>
        <span class="campus-track" aria-hidden="true"></span>
        <span class="campus-node campus-node--end">东南校区</span>
      </div>
    </section>

    <section class="status-panel" aria-live="polite">
      <div class="status-heading">
        <span class="section-index">系统状态</span>
        <span class="status-dot" :class="`status-dot--${state}`" aria-hidden="true"></span>
      </div>

      <div class="status-body">
        <p class="status-kicker">Phase 01 / 初始化</p>
        <h2>{{ statusLabel }}</h2>

        <template v-if="state === 'connected' && health">
          <p class="status-detail">
            {{ health.service }} 已响应，当前环境为
            <strong>{{ health.environment }}</strong>。
          </p>
          <dl class="service-facts">
            <div>
              <dt>API</dt>
              <dd>127.0.0.1:8000</dd>
            </div>
            <div>
              <dt>状态</dt>
              <dd>Ready</dd>
            </div>
          </dl>
        </template>

        <template v-else-if="state === 'error'">
          <p class="status-detail">
            请确认 FastAPI 已在 127.0.0.1:8000 启动，然后重新检查连接。
          </p>
          <button class="retry-button" type="button" @click="checkBackend">重新检查</button>
        </template>

        <p v-else class="status-detail">正在访问健康检查接口，请稍候。</p>
      </div>

      <footer class="status-footer">
        <span>Campus Activity Intelligence</span>
        <span>2026</span>
      </footer>
    </section>
  </main>
</template>
