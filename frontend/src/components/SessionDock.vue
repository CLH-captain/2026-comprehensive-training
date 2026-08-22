<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const roleLabel = computed(() => ({
  admin: '系统管理员',
  club_manager: '社团负责人',
  student: '学生用户',
}[auth.user?.role ?? 'student']))

async function logout(): Promise<void> {
  await auth.logout()
  await router.replace('/login')
}
</script>

<template>
  <div v-if="auth.user" class="session-dock">
    <span>{{ auth.user.username.slice(0, 1).toUpperCase() }}</span>
    <div><strong>{{ auth.user.username }}</strong><small>{{ roleLabel }}</small></div>
    <button type="button" @click="logout">退出</button>
  </div>
</template>

<style scoped>
.session-dock{position:fixed;right:22px;bottom:20px;z-index:25;display:flex;align-items:center;gap:10px;border:1px solid rgba(28,78,75,.16);border-radius:9px;padding:8px 9px 8px 8px;background:rgba(255,255,255,.94);box-shadow:0 10px 32px rgba(15,62,60,.13);backdrop-filter:blur(10px)}.session-dock>span{display:grid;place-items:center;width:32px;height:32px;border-radius:50%;color:#fff;background:#b77a31;font:13px Bahnschrift}.session-dock div{min-width:92px}.session-dock strong,.session-dock small{display:block}.session-dock strong{color:#294a49;font-size:10px}.session-dock small{margin-top:3px;color:#819391;font-size:8px}.session-dock button{border:0;border-left:1px solid #d9e2e0;padding:5px 3px 5px 10px;color:#53706e;background:none;cursor:pointer;font-size:9px}.session-dock button:hover{color:#9a5e20}
</style>
