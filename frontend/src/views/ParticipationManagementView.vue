<script setup lang="ts">
import axios from 'axios'
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { http } from '@/api/http'
import { useAuthStore } from '@/stores/auth'

interface ParticipationRecord {
  id: number
  activity_id: number
  activity_title: string
  club_id: number
  student_id: number
  student_no: string
  student_name: string
  status: string
  register_time?: string
  checkin_time?: string | null
}

const auth = useAuthStore()
const tab = ref<'registrations' | 'attendance'>('registrations')
const registrations = ref<ParticipationRecord[]>([])
const attendance = ref<ParticipationRecord[]>([])
const loading = ref(false)
const error = ref('')
const registerForm = reactive({ activity_id: '', student_id: '' })
const currentItems = computed(() => tab.value === 'registrations' ? registrations.value : attendance.value)

function statusLabel(status: string): string {
  return { registered: '有效报名', cancelled: '已取消', waitlisted: '候补', present: '到场', late: '迟到', absent: '缺席' }[status] ?? status
}
function formatTime(value?: string | null): string {
  return value ? new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) : '—'
}
async function loadRecords(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    const [registrationResponse, attendanceResponse] = await Promise.all([
      http.get<{ items: ParticipationRecord[] }>('/registrations'),
      http.get<{ items: ParticipationRecord[] }>('/attendance'),
    ])
    registrations.value = registrationResponse.data.items
    attendance.value = attendanceResponse.data.items
  } catch (reason) {
    error.value = axios.isAxiosError(reason) ? String(reason.response?.data?.message ?? '参与记录加载失败。') : '参与记录加载失败。'
  } finally { loading.value = false }
}
async function createRegistration(): Promise<void> {
  const studentId = auth.user?.role === 'student' ? auth.user.student_id : Number(registerForm.student_id)
  if (!studentId || !Number(registerForm.activity_id)) { error.value = '请填写有效的活动 ID 和学生 ID。'; return }
  try {
    await http.post('/registrations', { activity_id: Number(registerForm.activity_id), student_id: studentId })
    registerForm.activity_id = ''; registerForm.student_id = ''; await loadRecords()
  } catch (reason) { error.value = axios.isAxiosError(reason) ? String(reason.response?.data?.message ?? '报名失败。') : '报名失败。' }
}
async function updateRegistration(id: number, status: string): Promise<void> {
  await http.patch(`/registrations/${id}`, { status }); await loadRecords()
}
async function markAttendance(record: ParticipationRecord, status: string): Promise<void> {
  await http.put('/attendance', { activity_id: record.activity_id, student_id: record.student_id, status }); await loadRecords()
}

onMounted(loadRecords)
</script>

<template>
  <div class="workspace">
    <aside class="sidebar"><div class="brand"><span>S</span><div><strong>SZUT</strong><small>校园活动数据中心</small></div></div><nav><RouterLink to="/"><i>▦</i>数据总览</RouterLink><RouterLink to="/students"><i>◎</i>学生管理</RouterLink><RouterLink to="/clubs"><i>◇</i>社团管理</RouterLink><RouterLink to="/activities"><i>□</i>活动管理</RouterLink><RouterLink class="active" to="/participation"><i>✓</i>报名签到</RouterLink><RouterLink to="/analytics"><i>⌁</i>统计分析</RouterLink><RouterLink to="/agent"><i>✦</i>智能分析</RouterLink></nav><footer><b></b><div><strong>权限范围已生效</strong><small>{{ auth.user?.role }}</small></div></footer></aside>
    <main class="main"><header class="topbar"><div><p>活动执行数据 / 参与闭环</p><h1>报名与签到</h1></div><span>{{ auth.user?.username }}</span></header>
      <section class="intro"><div><small>PARTICIPATION LEDGER</small><h2>从报名意愿，到真实到场</h2><p>学生只查看本人记录，社团负责人只管理绑定社团，管理员可查看全部数据。</p></div><strong>{{ registrations.length }}<small> 条报名</small></strong></section>
      <section class="quick-register"><div><small>快速报名</small><h3>录入活动参与关系</h3></div><label>活动 ID<input v-model="registerForm.activity_id" type="number" min="1" /></label><label v-if="auth.user?.role !== 'student'">学生 ID<input v-model="registerForm.student_id" type="number" min="1" /></label><button type="button" @click="createRegistration">提交报名</button></section>
      <section class="panel"><header><div class="tabs"><button :class="{ active: tab === 'registrations' }" @click="tab='registrations'">报名记录 <b>{{ registrations.length }}</b></button><button :class="{ active: tab === 'attendance' }" @click="tab='attendance'">签到记录 <b>{{ attendance.length }}</b></button></div><button class="refresh" @click="loadRecords">刷新数据</button></header><p v-if="error" class="error">{{ error }}</p><div class="table-wrap" :class="{ loading }"><table><thead><tr><th>活动</th><th>学生</th><th>状态</th><th>记录时间</th><th>操作</th></tr></thead><tbody><tr v-for="item in currentItems" :key="item.id"><td><strong>{{ item.activity_title }}</strong><small>活动 ID {{ item.activity_id }}</small></td><td><strong>{{ item.student_name }}</strong><small>{{ item.student_no }}</small></td><td><span class="status" :class="`status--${item.status}`">{{ statusLabel(item.status) }}</span></td><td>{{ formatTime(tab === 'registrations' ? item.register_time : item.checkin_time) }}</td><td><div v-if="tab === 'registrations'" class="actions"><button v-if="item.status !== 'cancelled'" @click="updateRegistration(item.id,'cancelled')">取消</button><button v-if="auth.canManageClubs && item.status !== 'registered'" @click="updateRegistration(item.id,'registered')">设为有效</button></div><div v-else-if="auth.canManageClubs" class="actions"><button @click="markAttendance(item,'present')">到场</button><button @click="markAttendance(item,'late')">迟到</button><button @click="markAttendance(item,'absent')">缺席</button></div><span v-else>仅查看</span></td></tr></tbody></table><div v-if="!loading && !currentItems.length" class="empty">当前权限范围内暂无记录。</div></div></section>
    </main>
  </div>
</template>

<style scoped>
.workspace{min-height:100vh;color:#173737;background:#eef3f2}.sidebar{position:fixed;inset:0 auto 0 0;width:232px;display:flex;flex-direction:column;padding:28px 20px;color:#eaf6f3;background:#103f40}.brand{display:flex;align-items:center;gap:12px;padding:0 8px 28px;border-bottom:1px solid rgba(255,255,255,.12)}.brand>span{display:grid;place-items:center;width:38px;height:38px;border:1px solid #8ab3af;border-radius:50%;font:22px Georgia}.brand strong,.brand small{display:block}.brand strong{letter-spacing:.14em}.brand small{color:#a7cfca;font-size:10px}.sidebar nav{display:grid;gap:7px;margin-top:30px}.sidebar a{display:flex;align-items:center;gap:13px;border-radius:7px;padding:12px 14px;color:#b7d3d0;text-decoration:none;font-size:14px}.sidebar a i{width:18px;font-style:normal}.sidebar a.active,.sidebar a:hover{color:#fff;background:rgba(255,255,255,.1)}.sidebar a.active{box-shadow:inset 3px 0 #e1a354}.sidebar footer{display:flex;align-items:center;gap:10px;margin-top:auto;border-top:1px solid rgba(255,255,255,.12);padding:16px 8px 0}.sidebar footer>b{width:8px;height:8px;border-radius:50%;background:#75c9a6}.sidebar footer strong,.sidebar footer small{display:block;font-size:10px}.sidebar footer small{color:#8dbcb7}.main{margin-left:232px;padding:0 34px 48px}.topbar{display:flex;align-items:center;justify-content:space-between;min-height:96px}.topbar p{margin:0 0 6px;color:#7b8e8d;font-size:11px}.topbar h1{margin:0;font:600 28px STZhongsong,"Songti SC",serif}.topbar>span{color:#6d8482;font-size:11px}.intro{display:flex;align-items:center;justify-content:space-between;border-radius:9px;padding:28px 34px;color:#fff;background:linear-gradient(105deg,#105a56,#26766f)}.intro small{color:#e3b26f;font-size:9px;letter-spacing:.14em}.intro h2{margin:8px 0 6px;font:500 25px STZhongsong}.intro p{margin:0;color:#cce2de;font-size:12px}.intro>strong{font:35px Bahnschrift}.intro>strong small{color:#b9d7d2}.quick-register{display:flex;align-items:end;gap:14px;margin:16px 0;border:1px solid #d6e0de;border-radius:8px;padding:17px 20px;background:#fff}.quick-register>div{margin-right:auto}.quick-register small{color:#b7782d;font-size:9px}.quick-register h3{margin:4px 0 0;font-size:15px}.quick-register label{display:grid;gap:5px;color:#718583;font-size:9px}.quick-register input{width:130px;height:36px;border:1px solid #ccd9d6;border-radius:5px;padding:0 9px}.quick-register button,.actions button,.refresh{height:36px;border:1px solid #17615d;border-radius:5px;padding:0 13px;color:#17615d;background:#fff;cursor:pointer}.quick-register>button{color:#fff;background:#17615d}.panel{border:1px solid #d6e0de;border-radius:8px;padding:21px;background:#fff}.panel>header{display:flex;justify-content:space-between;border-bottom:1px solid #e1e8e6;padding-bottom:14px}.tabs{display:flex;gap:6px}.tabs button{border:0;border-radius:5px;padding:9px 13px;color:#617876;background:#edf3f2}.tabs button.active{color:#fff;background:#17615d}.tabs b{margin-left:5px}.refresh{height:33px}.table-wrap{min-height:280px;overflow:auto}.table-wrap.loading{opacity:.5}table{width:100%;border-collapse:collapse}th{height:42px;color:#8b9a98;font-size:10px;text-align:left}td{height:61px;border-top:1px solid #edf1f0;color:#647876;font-size:11px}td strong,td small{display:block}td strong{color:#2e4d4c}td small{margin-top:4px;color:#96a4a2;font-size:9px}.status{border-radius:9px;padding:4px 8px;font-size:9px}.status--registered,.status--present{color:#176a61;background:#e4f2ef}.status--late,.status--waitlisted{color:#95611d;background:#fff0d9}.status--cancelled,.status--absent{color:#8c5555;background:#f4e5e5}.actions{display:flex;gap:5px}.actions button{height:29px;padding:0 8px;font-size:9px}.empty{padding:70px;text-align:center;color:#879997}.error{border-left:3px solid #bd7f34;padding:10px;color:#8c5720;background:#fff6ea;font-size:11px}
</style>
