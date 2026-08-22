<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import SessionDock from '@/components/SessionDock.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

async function handleExpired(): Promise<void> {
  auth.clear()
  if (route.name !== 'login') await router.replace({ name: 'login', query: { redirect: route.fullPath } })
}

onMounted(async () => {
  window.addEventListener('szut-auth-expired', handleExpired)
  if (auth.isAuthenticated && !auth.user) await auth.restore()
})
onBeforeUnmount(() => window.removeEventListener('szut-auth-expired', handleExpired))
</script>

<template>
  <RouterView />
  <SessionDock v-if="route.name !== 'login'" />
</template>