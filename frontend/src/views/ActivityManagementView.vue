<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import { http } from '@/api/http'
import ActivityFormDialog from '@/components/activities/ActivityFormDialog.vue'
import { useAuthStore } from '@/stores/auth'
import type { ActivityDetail, ActivityListResponse } from '@/types/activity'

const auth = useAuthStore()
const formOpen = ref(false)
const selectedActivity = ref<ActivityListResponse['items'][number] | null>(null)
const data = ref<ActivityListResponse | null>(null)
const detail = ref<ActivityDetail | null>(null)
const loading = ref(true)
const detailLoading = ref(false)
const page = ref(1)
const pageSize = 15
const search = ref('')
const termId = ref('')
const categoryId = ref('')
const clubId = ref('')
const campusId = ref('')
const status = ref('')
let timer: ReturnType<typeof setTimeout> | undefined
const formatter = new Intl.NumberFormat('zh-CN')
const totalPages = computed(() => Math.max(1, Math.ceil((data.value?.total ?? 0) / pageSize)))
const cards = computed(() => [
  { label: '活动总量', value: data.value?.summary.total_activities ?? 0, note: '覆盖完整学年', mark: '总' },
  { label: '已完成活动', value: data.value?.summary.completed_activities ?? 0, note: '统计有效活动', mark: '完' },
  { label: '有效报名', value: data.value?.summary.registrations ?? 0, note: '报名状态正常', mark: '报' },
  { label: '实际到场', value: data.value?.summary.attendance ?? 0, note: '到场与迟到合计', mark: '到' },
])

async function loadActivities(): Promise<void> {
  loading.value = true
  try {
    data.value = (await http.get<ActivityListResponse>('/activities', { params: { page: page.value, page_size: pageSize, search: search.value || undefined, term_id: termId.value || undefined, category_id: categoryId.value || undefined, club_id: clubId.value || undefined, campus_id: campusId.value || undefined, status: status.value || undefined } })).data
  } finally {
    loading.value = false
  }
}
async function openDetail(id: number): Promise<void> {
  selectedActivity.value = data.value?.items.find((item) => item.id === id) ?? null
  detail.value = null
  detailLoading.value = true
  try { detail.value = (await http.get<ActivityDetail>(`/activities/${id}`)).data } finally { detailLoading.value = false }
}

function createActivity(): void {
  selectedActivity.value = null
  formOpen.value = true
}
function editActivity(): void { formOpen.value = true }
async function cancelActivity(): Promise<void> {
  if (!detail.value || !window.confirm(`确定取消活动“${detail.value.title}”吗？`)) return
  await http.delete(`/activities/${detail.value.id}`)
  detail.value = null
  await loadActivities()
}
async function activitySaved(): Promise<void> {
  formOpen.value = false
  detail.value = null
  await loadActivities()
}
function resetFilters(): void {
  search.value = ''; termId.value = ''; categoryId.value = ''; clubId.value = ''; campusId.value = ''; status.value = ''; page.value = 1; void loadActivities()
}
function changePage(next: number): void {
  if (next < 1 || next > totalPages.value) return
  page.value = next; void loadActivities()
}
function formatDate(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date(value))
}
function formatTime(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(value))
}
function statusLabel(value: string): string {
  return { draft: '草稿', published: '已发布', completed: '已完成', cancelled: '已取消', registered: '有效报名', waitlisted: '候补', present: '到场', late: '迟到', absent: '缺席' }[value] ?? value
}
function capacityRate(registrations: number, capacity: number): number {
  return Math.min(100, Math.round(registrations / capacity * 100))
}

watch([termId, categoryId, clubId, campusId, status], () => { page.value = 1; void loadActivities() })
watch(search, () => { if (timer) clearTimeout(timer); timer = setTimeout(() => { page.value = 1; void loadActivities() }, 300) })
onMounted(loadActivities)
</script>

<template>
  <div class="workspace">
    <aside class="sidebar"><div class="brand"><span>S</span><div><strong>SZUT</strong><small>校园活动数据中心</small></div></div><nav><RouterLink to="/"><i>▦</i>数据总览</RouterLink><RouterLink to="/students"><i>◎</i>学生管理</RouterLink><RouterLink to="/clubs"><i>◇</i>社团管理</RouterLink><RouterLink class="active" to="/activities"><i>□</i>活动管理</RouterLink><RouterLink to="/participation"><i>✓</i>报名签到</RouterLink><RouterLink to="/analytics"><i>⌁</i>统计分析</RouterLink><a><i>✦</i>智能分析</a></nav><footer><b></b><div><strong>系统运行正常</strong><small>活动数据已连接</small></div></footer></aside>
    <main class="main">
      <header class="topbar"><div><p>校园活动数据 / 活动全周期</p><h1>活动管理</h1></div><div class="admin"><span>2025—2026 学年</span><b>管</b></div></header>
      <section class="intro"><div><small>ACTIVITY OPERATIONS</small><h2>从发布到签到，掌握每场活动进程</h2><p>统一查看活动时间、场地容量、报名情况与真实到场表现。</p></div><div><strong>{{ formatter.format(data?.total ?? 0) }}</strong><span>当前筛选活动</span></div></section>
      <section class="cards"><article v-for="card in cards" :key="card.label"><i>{{ card.mark }}</i><div><span>{{ card.label }}</span><strong>{{ formatter.format(card.value) }}</strong><small>{{ card.note }}</small></div></article></section>
      <section class="panel"><header class="panel-head"><div><small>活动检索</small><h3>活动运行台账</h3></div><div class="panel-actions"><span>共 {{ data?.total ?? 0 }} 场</span><button v-if="auth.canManageClubs" type="button" @click="createActivity">＋ 新建活动</button></div></header>
        <div class="filters"><label><i>⌕</i><input v-model.trim="search" placeholder="搜索活动、编号或社团" /></label><select v-model="termId"><option value="">全部学期</option><option v-for="item in data?.options.terms" :key="item.id" :value="String(item.id)">{{ item.name }}</option></select><select v-model="categoryId"><option value="">全部类别</option><option v-for="item in data?.options.categories" :key="item.id" :value="String(item.id)">{{ item.name }}</option></select><select v-model="clubId"><option value="">全部社团</option><option v-for="item in data?.options.clubs" :key="item.id" :value="String(item.id)">{{ item.name }}</option></select><select v-model="campusId"><option value="">全部校区</option><option v-for="item in data?.options.campuses" :key="item.id" :value="String(item.id)">{{ item.name }}</option></select><select v-model="status"><option value="">全部状态</option><option value="completed">已完成</option><option value="cancelled">已取消</option><option value="published">已发布</option><option value="draft">草稿</option></select><button @click="resetFilters">重置</button></div>
        <div class="table-wrap" :class="{ faded: loading }"><table><thead><tr><th>活动名称</th><th>社团 / 类别</th><th>时间</th><th>场地</th><th>容量使用</th><th>到场</th><th>状态</th><th></th></tr></thead><tbody><tr v-for="item in data?.items" :key="item.id" @click="openDetail(item.id)"><td><div class="activity-name"><i>{{ item.start_time.slice(5,7) }}</i><div><strong>{{ item.title }}</strong><small>{{ item.code }}</small></div></div></td><td><strong>{{ item.club_name }}</strong><small>{{ item.category_name }}</small></td><td><strong>{{ formatTime(item.start_time) }}</strong><small>{{ item.term_name }}</small></td><td><strong>{{ item.venue_name }}</strong><small>{{ item.campus_name }}</small></td><td><div class="capacity"><span><b>{{ item.registrations }}</b> / {{ item.capacity }}</span><div><i :style="{width:`${capacityRate(item.registrations,item.capacity)}%`}"></i></div></div></td><td><b class="accent">{{ item.attendance }}</b><small>{{ item.attendance_rate ?? '—' }}%</small></td><td><span class="status" :class="`status--${item.status}`">{{ statusLabel(item.status) }}</span></td><td><button @click.stop="openDetail(item.id)">查看详情</button></td></tr></tbody></table></div>
        <footer class="pager"><span>第 {{ page }} / {{ totalPages }} 页</span><div><button :disabled="page===1" @click="changePage(page-1)">上一页</button><b>{{ page }}</b><button :disabled="page===totalPages" @click="changePage(page+1)">下一页</button></div></footer>
      </section>
    </main>

    <div v-if="detailLoading || detail" class="mask" @click.self="detail=null"><aside class="drawer"><button class="close" @click="detail=null">×</button><p v-if="detailLoading" class="loading">正在读取活动详情…</p><template v-else-if="detail">
      <header class="profile"><span class="status" :class="`status--${detail.status}`">{{ statusLabel(detail.status) }}</span><small>{{ detail.category_name }} · {{ detail.code }}</small><h2>{{ detail.title }}</h2><p>{{ detail.club_name }}</p></header>
      <div class="timeline"><div class="done"><i></i><span>创建</span><small>{{ formatDate(detail.created_at) }}</small></div><div class="done"><i></i><span>报名</span><small>{{ detail.metrics.registrations }} 人</small></div><div class="done"><i></i><span>开展</span><small>{{ formatDate(detail.start_time) }}</small></div><div :class="{done:detail.status==='completed'}"><i></i><span>完成</span><small>{{ statusLabel(detail.status) }}</small></div></div>
      <p class="description">{{ detail.description }}</p>
      <dl class="facts"><div><dt>活动时间</dt><dd>{{ formatTime(detail.start_time) }} — {{ formatTime(detail.end_time).slice(6) }}</dd></div><div><dt>举办地点</dt><dd>{{ detail.campus_name }} · {{ detail.venue_name }}</dd></div><div><dt>所属学期</dt><dd>{{ detail.term_name }}</dd></div><div><dt>活动容量</dt><dd>{{ detail.capacity }} 人</dd></div></dl>
      <section class="metrics"><div><b>{{ detail.metrics.registrations }}</b><span>有效报名</span></div><div><b>{{ detail.metrics.attendance }}</b><span>实际到场</span></div><div><b>{{ detail.metrics.absent }}</b><span>未到场</span></div><div><b>{{ detail.metrics.attendance_rate ?? '—' }}%</b><span>到场率</span></div></section>
      <div v-if="auth.canManageClubs" class="profile-actions"><button type="button" @click="editActivity">编辑活动</button><button class="danger" type="button" @click="cancelActivity">取消活动</button></div><section class="drawer-section"><header><h3>报名与签到结构</h3><span>实时聚合</span></header><div class="distribution"><div><h4>报名状态</h4><p v-for="item in detail.registration_distribution" :key="item.status"><span>{{ statusLabel(item.status) }}</span><b>{{ item.count }}</b></p></div><div><h4>签到状态</h4><p v-for="item in detail.attendance_distribution" :key="item.status"><span>{{ statusLabel(item.status) }}</span><b>{{ item.count }}</b></p></div></div></section>
      <section class="drawer-section"><header><h3>参与学生预览</h3><span>前 {{ detail.participants.length }} 条</span></header><div class="participants"><div v-for="item in detail.participants" :key="item.id"><i>{{ item.name.slice(-1) }}</i><div><b>{{ item.name }}</b><small>{{ item.student_no }} · {{ item.college_name }}</small></div><span :class="`attend attend--${item.attendance_status}`">{{ item.attendance_status ? statusLabel(item.attendance_status) : statusLabel(item.registration_status) }}</span></div></div></section>
    </template></aside></div>
  </div>
  <ActivityFormDialog :open="formOpen" :activity="selectedActivity" :options="data?.options" @close="formOpen = false" @saved="activitySaved" />
</template>

<style scoped>
.workspace{min-height:100vh;background:#eef3f2;color:#173237}.sidebar{position:fixed;inset:0 auto 0 0;width:232px;display:flex;flex-direction:column;padding:28px 20px;background:#103f40;color:#eaf6f3}.brand{display:flex;align-items:center;gap:12px;padding:0 8px 28px;border-bottom:1px solid rgba(255,255,255,.12)}.brand>span{display:grid;place-items:center;width:38px;height:38px;border:1px solid #8ab3af;border-radius:50%;font:22px Georgia}.brand strong,.brand small{display:block}.brand strong{letter-spacing:.14em}.brand small{color:#a7cfca;font-size:10px}.sidebar nav{display:grid;gap:7px;margin-top:30px}.sidebar nav a{display:flex;align-items:center;gap:13px;border-radius:7px;padding:12px 14px;color:#b7d3d0;text-decoration:none;font-size:14px}.sidebar nav i{width:18px;font-style:normal}.sidebar nav .active,.sidebar nav a:hover{color:#fff;background:rgba(255,255,255,.1)}.sidebar nav .active{box-shadow:inset 3px 0 #e1a354}.sidebar footer{display:flex;align-items:center;gap:10px;margin-top:auto;padding:16px 8px 0;border-top:1px solid rgba(255,255,255,.12)}.sidebar footer>b{width:8px;height:8px;border-radius:50%;background:#75c9a6}.sidebar footer strong,.sidebar footer small{display:block;font-size:11px}.sidebar footer small{color:#82b5af}.main{margin-left:232px;padding:0 34px 48px}.topbar{display:flex;align-items:center;justify-content:space-between;min-height:96px}.topbar p{margin:0 0 6px;color:#7b8e8d;font-size:12px}.topbar h1{margin:0;font:600 28px STZhongsong,"Songti SC",serif}.admin{display:flex;align-items:center;gap:16px;color:#718684;font-size:11px}.admin b{display:grid;place-items:center;width:38px;height:38px;border-radius:50%;color:#fff;background:#bd7f34}.intro{display:flex;align-items:center;justify-content:space-between;min-height:150px;border:1px solid #d7e0de;border-radius:9px;padding:25px 34px;background:#fff}.intro small,.panel-head small{color:#bd7f34;font-size:10px;font-weight:700;letter-spacing:.13em}.intro h2{margin:9px 0 7px;font:600 25px STZhongsong,"Songti SC",serif}.intro p{margin:0;color:#718482;font-size:13px}.intro>div:last-child{min-width:180px;border-left:1px solid #dce5e3;padding-left:32px}.intro>div:last-child strong,.intro>div:last-child span{display:block}.intro>div:last-child strong{font:36px Bahnschrift}.intro>div:last-child span{color:#899b99;font-size:11px}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:16px 0}.cards article{display:flex;align-items:center;gap:14px;border:1px solid #d7e0de;border-radius:8px;padding:17px;background:#fff}.cards article>i{display:grid;place-items:center;width:38px;height:38px;border-radius:50%;color:#17615d;background:#e5f1ef;font:normal 16px STZhongsong}.cards span,.cards strong,.cards small{display:block}.cards span{color:#718482;font-size:11px}.cards strong{margin:3px 0;font:23px Bahnschrift}.cards small{color:#9aa8a7;font-size:9px}.panel{border:1px solid #d7e0de;border-radius:9px;padding:22px;background:#fff}.panel-head{display:flex;justify-content:space-between}.panel-head h3{margin:5px 0 0;font-size:18px}.panel-head>span{color:#8a9a98;font-size:11px}.filters{display:grid;grid-template-columns:1.35fr repeat(5,minmax(100px,.7fr)) auto;gap:8px;margin:20px 0 15px}.filters label{position:relative}.filters label i{position:absolute;left:11px;top:8px;font-style:normal}.filters input,.filters select{width:100%;height:38px;border:1px solid #d3dddb;border-radius:6px;padding:0 9px;color:#344e4f;background:#f9fbfa;font-size:11px}.filters input{padding-left:34px}.filters>button,.pager button,td button{border:1px solid #bdcbc8;border-radius:5px;color:#17615d;background:#fff;cursor:pointer}.table-wrap{overflow-x:auto;border-top:1px solid #e3e9e8}.faded{opacity:.5}table{width:100%;border-collapse:collapse;white-space:nowrap}th{height:42px;color:#899a98;font-size:10px;text-align:left}td{height:65px;border-top:1px solid #edf1f0;color:#627674;font-size:11px}tbody tr{cursor:pointer}tbody tr:hover{background:#f4f9f8}.activity-name{display:flex;align-items:center;gap:10px}.activity-name>i{display:grid;place-items:center;width:34px;height:34px;border-radius:7px;color:#fff;background:#397c77;font:normal 13px Bahnschrift}.activity-name strong,.activity-name small,td>strong,td>small{display:block;max-width:230px;overflow:hidden;text-overflow:ellipsis}.activity-name strong,td>strong{color:#294746}.activity-name small,td>small{margin-top:4px;color:#90a09e;font-size:9px}.capacity{width:90px}.capacity>span{font-size:9px}.capacity>div{height:5px;margin-top:5px;border-radius:3px;background:#e1e9e7}.capacity i{display:block;height:100%;border-radius:3px;background:#4d988e}.accent{display:block;color:#b97428;font:16px Bahnschrift}.status{display:inline-block;border-radius:9px;padding:4px 8px;font-size:9px}.status--completed{color:#1a6c63;background:#e3f2ef}.status--cancelled{color:#955353;background:#f5e5e5}.status--published{color:#336c88;background:#e6f0f5}.status--draft{color:#776a55;background:#eeece7}td button{padding:6px 9px}.pager{display:flex;justify-content:space-between;border-top:1px solid #e6ecea;padding-top:15px;color:#869694;font-size:10px}.pager div{display:flex;gap:5px}.pager button{height:30px;padding:0 11px}.pager b{display:grid;place-items:center;width:30px;border-radius:5px;color:#fff;background:#17615d}.mask{position:fixed;inset:0;z-index:30;background:rgba(11,42,42,.38);backdrop-filter:blur(2px)}.drawer{position:absolute;inset:0 0 0 auto;width:min(580px,100%);overflow-y:auto;padding:34px;background:#f8fbfa;box-shadow:-18px 0 50px rgba(10,45,44,.14)}.close{position:absolute;right:22px;top:18px;border:0;color:#718482;background:none;font-size:27px}.loading{display:grid;place-items:center;height:60vh}.profile{border-bottom:1px solid #dbe4e2;padding:12px 40px 22px 0}.profile>small{display:block;margin-top:10px;color:#a36e2d;font-size:9px}.profile h2{margin:6px 0 4px;font:600 24px STZhongsong}.profile p,.description{margin:0;color:#768987;font-size:11px}.timeline{display:grid;grid-template-columns:repeat(4,1fr);padding:21px 4px 17px}.timeline>div{position:relative;text-align:center}.timeline>div:before{position:absolute;left:-50%;top:5px;width:100%;height:1px;background:#d4dfdd;content:""}.timeline>div:first-child:before{display:none}.timeline i{position:relative;z-index:1;display:block;width:10px;height:10px;margin:0 auto 6px;border:2px solid #a9bab7;border-radius:50%;background:#f8fbfa}.timeline .done i{border-color:#3c9187;background:#3c9187}.timeline span,.timeline small{display:block;font-size:9px}.timeline small{margin-top:3px;color:#96a5a3}.description{padding:11px 2px 16px;line-height:1.7}.facts{display:grid;grid-template-columns:1fr 1fr;gap:1px;margin:0 0 16px;border:1px solid #dce5e3;background:#dce5e3}.facts div{padding:11px 13px;background:#fff}.facts dt{color:#92a19f;font-size:9px}.facts dd{margin:4px 0 0;font-size:11px}.metrics{display:grid;grid-template-columns:repeat(4,1fr);padding:16px 8px;border-radius:7px;color:#fff;background:#174f4d}.metrics div{text-align:center}.metrics div+div{border-left:1px solid rgba(255,255,255,.15)}.metrics b,.metrics span{display:block}.metrics b{font:20px Bahnschrift}.metrics span{margin-top:4px;color:#acd0cb;font-size:9px}.drawer-section{margin-top:24px}.drawer-section>header{display:flex;justify-content:space-between;border-bottom:1px solid #dae4e2;padding-bottom:9px}.drawer-section h3{margin:0;font-size:14px}.drawer-section header span{color:#8d9d9b;font-size:9px}.distribution{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:12px}.distribution>div{border:1px solid #dde6e4;border-radius:6px;padding:12px;background:#fff}.distribution h4{margin:0 0 8px;color:#607674;font-size:10px}.distribution p{display:flex;justify-content:space-between;margin:0;padding:6px 0;border-top:1px solid #edf1f0;font-size:10px}.participants>div{display:flex;align-items:center;gap:10px;border-bottom:1px solid #e5ebe9;padding:10px 2px}.participants>div>i{display:grid;place-items:center;width:28px;height:28px;border-radius:50%;color:#fff;background:#529188;font-style:normal;font-size:10px}.participants>div>div{min-width:0;flex:1}.participants b,.participants small{display:block}.participants b{font-size:11px}.participants small{margin-top:3px;color:#91a09e;font-size:9px}.attend{border-radius:8px;padding:3px 7px;font-size:8px}.attend--present{color:#1b6f65;background:#e4f3ef}.attend--late{color:#9a651f;background:#fff0dc}.attend--absent{color:#8b5f5f;background:#f5e7e7}@media(max-width:1200px){.cards{grid-template-columns:1fr 1fr}.filters{grid-template-columns:1fr 1fr 1fr 1fr}}@media(max-width:760px){.sidebar{position:static;width:auto}.sidebar nav,.sidebar footer{display:none}.main{margin-left:0;padding:0 14px 30px}.intro>div:last-child{display:none}.cards{grid-template-columns:1fr 1fr}.filters{grid-template-columns:1fr}}@media(max-width:440px){.cards{grid-template-columns:1fr}}
.panel-actions{display:flex;align-items:center;gap:13px}.panel-actions button,.profile-actions button{border:1px solid #17615d;border-radius:5px;padding:8px 12px;color:#fff;background:#17615d;cursor:pointer;font-size:10px}.profile-actions{display:flex;gap:8px;margin:15px 0}.profile-actions .danger{border-color:#b77b69;color:#8b4e3e;background:#fff}
</style>
