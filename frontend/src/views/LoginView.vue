<script setup lang="ts">
import axios from 'axios'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import campusPhoto from '@/assets/campus/zichuan-bridge.jpg'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const username = ref('admin')
const password = ref('')
const error = ref('')

async function submit(): Promise<void> {
  error.value = ''
  try {
    await auth.login(username.value.trim(), password.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    await router.replace(redirect)
  } catch (reason) {
    if (axios.isAxiosError(reason) && reason.response?.status === 401) {
      error.value = '用户名或密码不正确，请重新输入。'
    } else {
      error.value = '暂时无法连接后端服务，请确认系统已经启动。'
    }
  }
}
</script>

<template>
  <main class="login-page">
    <section class="campus-side" :style="{ backgroundImage: `linear-gradient(145deg, rgba(8,55,53,.9), rgba(18,63,64,.84)), url(${campusPhoto})` }">
      <div class="school-mark"><span>S</span><div><strong>SZUT</strong><small>苏州工学院</small></div></div>
      <div class="campus-copy">
        <span>CLUB ACTIVITY DATA CENTER</span>
        <h1>让校园里的<br />每一次参与都有迹可循</h1>
        <p>社团、活动、报名与签到统一管理，以真实数据理解校园活力。</p>
      </div>
      <footer><span>苏州 · 常熟</span><i></i><span>2025—2026</span></footer>
    </section>

    <section class="login-side">
      <form @submit.prevent="submit">
        <span class="section-no">01 / ACCOUNT</span>
        <h2>登录校园活动数据中心</h2>
        <p>使用管理员、社团负责人或学生演示账号进入系统。</p>
        <label><span>用户名</span><input v-model="username" autocomplete="username" maxlength="50" required /></label>
        <label><span>密码</span><input v-model="password" type="password" autocomplete="current-password" maxlength="200" required /></label>
        <div v-if="error" class="login-error">{{ error }}</div>
        <button type="submit" :disabled="auth.loading">{{ auth.loading ? '正在验证…' : '进入系统' }}</button>
        <div class="demo-note"><strong>课程演示账号</strong><span>admin · club_manager_demo · student_demo</span><small>密码使用本机 .env 配置，不写入页面。</small></div>
      </form>
    </section>
  </main>
</template>

<style scoped>
.login-page{display:grid;grid-template-columns:minmax(520px,1.12fr) minmax(440px,.88fr);min-height:100vh;background:#f5f8f7;color:#183536}.campus-side{position:relative;display:flex;flex-direction:column;overflow:hidden;padding:48px 62px;color:#f7fbfa;background-position:center;background-size:cover}.campus-side:before{position:absolute;inset:auto -120px -220px auto;width:620px;height:620px;border:1px solid rgba(255,255,255,.16);border-radius:50%;box-shadow:0 0 0 70px rgba(255,255,255,.035),0 0 0 150px rgba(255,255,255,.025);content:""}.school-mark{display:flex;align-items:center;gap:13px}.school-mark>span{display:grid;place-items:center;width:43px;height:43px;border:1px solid #a8cfca;border-radius:50%;font:24px Georgia}.school-mark strong,.school-mark small{display:block}.school-mark strong{letter-spacing:.17em}.school-mark small{margin-top:3px;color:#b7d5d1;font-size:10px;letter-spacing:.14em}.campus-copy{position:relative;z-index:1;margin:auto 0;max-width:650px}.campus-copy>span,.section-no{color:#d8aa68;font-size:10px;font-weight:700;letter-spacing:.2em}.campus-copy h1{margin:20px 0 22px;font:500 clamp(42px,5vw,72px)/1.2 STZhongsong,"Songti SC",serif;letter-spacing:-.04em}.campus-copy p{max-width:510px;color:#c5ddda;font-size:15px;line-height:1.9}.campus-side footer{position:relative;z-index:1;display:flex;align-items:center;gap:14px;color:#a9cbc7;font:10px Bahnschrift;letter-spacing:.14em}.campus-side footer i{width:70px;height:1px;background:#7fa9a5}.login-side{display:grid;place-items:center;padding:64px}.login-side form{width:min(100%,440px)}.login-side h2{margin:18px 0 10px;font:600 30px STZhongsong,"Songti SC",serif}.login-side form>p{margin:0 0 36px;color:#718583;font-size:13px}.login-side label{display:grid;gap:8px;margin-top:18px;color:#5d7472;font-size:11px}.login-side input{height:48px;border:1px solid #cad8d5;border-radius:5px;padding:0 14px;color:#203f3f;background:#fff;outline:none}.login-side input:focus{border-color:#36877f;box-shadow:0 0 0 3px rgba(54,135,127,.1)}.login-side button{width:100%;height:50px;margin-top:24px;border:0;border-radius:5px;color:#fff;background:#0f5c58;cursor:pointer;font-weight:600;letter-spacing:.08em}.login-side button:disabled{opacity:.65}.login-error{margin-top:16px;border-left:3px solid #bd7f34;padding:9px 12px;color:#8c5720;background:#fff6ea;font-size:12px}.demo-note{display:grid;gap:5px;margin-top:26px;border-top:1px solid #d9e2e0;padding-top:20px;color:#748886;font-size:11px}.demo-note strong{color:#30504f}.demo-note small{color:#9aa8a7}
</style>
