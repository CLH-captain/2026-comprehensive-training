<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import { http } from '@/api/http'
import type { ClubDetail, ClubListResponse } from '@/types/club'

const data = ref<ClubListResponse | null>(null)
const detail = ref<ClubDetail | null>(null)
const loading = ref(true)
const detailLoading = ref(false)
const error = ref('')
const page = ref(1)
const pageSize = 15
const search = ref('')
const categoryId = ref('')
const campusId = ref('')
const status = ref('active')
let searchTimer: ReturnType<typeof setTimeout> | undefined
const formatNumber = new Intl.NumberFormat('zh-CN')
const totalPages = computed(() => Math.max(1, Math.ceil((data.value?.total ?? 0) / pageSize)))
const cards = computed(() => [
  { label: '正常运行社团', value: data.value?.summary.active_clubs ?? 0, note: '覆盖两校区', mark: '社' },
  { label: '社团类别', value: data.value?.summary.category_count ?? 0, note: '多元校园兴趣', mark: '类' },
  { label: '成员关系', value: data.value?.summary.memberships ?? 0, note: '活跃成员记录', mark: '员' },
  { label: '已开展活动', value: data.value?.summary.completed_activities ?? 0, note: '2025—2026 学年', mark: '活' },
])

async function loadClubs(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    data.value = (await http.get<ClubListResponse>('/clubs', { params: { page: page.value, page_size: pageSize, search: search.value || undefined, category_id: categoryId.value || undefined, campus_id: campusId.value || undefined, status: status.value || undefined } })).data
  } catch {
    error.value = '社团数据加载失败，请检查后端服务。'
  } finally {
    loading.value = false
  }
}

async function openDetail(id: number): Promise<void> {
  detail.value = null
  detailLoading.value = true
  try {
    detail.value = (await http.get<ClubDetail>(`/clubs/${id}`)).data
  } finally {
    detailLoading.value = false
  }
}

function resetFilters(): void {
  search.value = ''
  categoryId.value = ''
  campusId.value = ''
  status.value = 'active'
  page.value = 1
  void loadClubs()
}
function changePage(next: number): void {
  if (next < 1 || next > totalPages.value) return
  page.value = next
  void loadClubs()
}
function formatDate(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date(value))
}
function roleLabel(role: string): string {
  return { leader: '负责人', core: '骨干成员', member: '普通成员' }[role] ?? role
}

watch([categoryId, campusId, status], () => { page.value = 1; void loadClubs() })
watch(search, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; void loadClubs() }, 300)
})
onMounted(loadClubs)
</script>

<template>
  <div class="workspace">
    <aside class="sidebar">
      <div class="brand"><span class="brand-seal">S</span><div><strong>SZUT</strong><small>校园活动数据中心</small></div></div>
      <nav>
        <RouterLink class="nav-item" to="/"><span>▦</span>数据总览</RouterLink>
        <RouterLink class="nav-item" to="/students"><span>◎</span>学生管理</RouterLink>
        <RouterLink class="nav-item nav-item--active" to="/clubs"><span>◇</span>社团管理</RouterLink>
        <span class="nav-item"><span>□</span>活动管理</span><span class="nav-item"><span>⌁</span>统计分析</span><span class="nav-item"><span>✦</span>智能分析</span>
      </nav>
      <div class="sidebar-foot"><i></i><div><strong>系统运行正常</strong><small>社团数据已连接</small></div></div>
    </aside>

    <main class="main">
      <header class="topbar"><div><p>校园组织数据 / 社团档案</p><h1>社团管理</h1></div><div class="top-meta"><span>2025—2026 学年</span><b>管</b></div></header>
      <section class="intro"><div><small>CLUB DIRECTORY</small><h2>连接兴趣、组织与校园活力</h2><p>查看社团成员规模、活动产出与实际参与表现，理解校园组织的活跃结构。</p></div><div class="intro-total"><strong>{{ formatNumber.format(data?.total ?? 0) }}</strong><span>当前筛选结果</span></div></section>
      <section class="cards"><article v-for="card in cards" :key="card.label"><i>{{ card.mark }}</i><div><span>{{ card.label }}</span><strong>{{ formatNumber.format(card.value) }}</strong><small>{{ card.note }}</small></div></article></section>

      <section class="panel">
        <header class="panel-head"><div><small>社团检索</small><h3>社团运行名单</h3></div><span>共 {{ data?.total ?? 0 }} 个社团</span></header>
        <div class="filters"><label><i>⌕</i><input v-model.trim="search" placeholder="搜索社团名称或编号" /></label><select v-model="categoryId"><option value="">全部类别</option><option v-for="item in data?.options.categories" :key="item.id" :value="String(item.id)">{{ item.name }}</option></select><select v-model="campusId"><option value="">全部校区</option><option v-for="item in data?.options.campuses" :key="item.id" :value="String(item.id)">{{ item.name }}</option></select><select v-model="status"><option value="">全部状态</option><option value="active">正常运行</option><option value="inactive">已停用</option></select><button @click="resetFilters">重置</button></div>
        <div v-if="error" class="error">{{ error }}</div>
        <div v-else class="table-wrap" :class="{ faded: loading }">
          <table><thead><tr><th>社团名称</th><th>类别 / 校区</th><th>指导老师</th><th>学生负责人</th><th>成员</th><th>活动</th><th>参与人次</th><th></th></tr></thead><tbody>
            <tr v-for="club in data?.items" :key="club.id" @click="openDetail(club.id)"><td><div class="club-name"><i>{{ club.name.slice(0, 1) }}</i><div><strong>{{ club.name }}</strong><small>{{ club.code }}</small></div></div></td><td><strong>{{ club.category_name }}</strong><small>{{ club.campus_name }}</small></td><td>{{ club.advisor_name }}</td><td>{{ club.leader_name }}</td><td><b>{{ club.member_count }}</b><small> 人</small></td><td><b>{{ club.activity_count }}</b><small> 场</small></td><td><b class="accent">{{ club.participation_count }}</b><small> 人次</small></td><td><button @click.stop="openDetail(club.id)">查看详情</button></td></tr>
          </tbody></table>
        </div>
        <footer class="pager"><span>第 {{ page }} / {{ totalPages }} 页</span><div><button :disabled="page===1" @click="changePage(page-1)">上一页</button><b>{{ page }}</b><button :disabled="page===totalPages" @click="changePage(page+1)">下一页</button></div></footer>
      </section>
    </main>

    <div v-if="detailLoading || detail" class="mask" @click.self="detail=null"><aside class="drawer"><button class="close" @click="detail=null">×</button><p v-if="detailLoading" class="loading">正在读取社团档案…</p><template v-else-if="detail">
      <header class="profile"><i>{{ detail.name.slice(0,1) }}</i><div><small>{{ detail.category_name }} · {{ detail.campus_name }}</small><h2>{{ detail.name }}</h2><p>{{ detail.code }} · 成立于 {{ formatDate(detail.founded_date) }}</p></div></header>
      <p class="description">{{ detail.description }}</p>
      <dl class="facts"><div><dt>指导老师</dt><dd>{{ detail.advisor_name }}</dd></div><div><dt>学生负责人</dt><dd>{{ detail.leader_name }} · {{ detail.leader_student_no }}</dd></div></dl>
      <section class="metrics"><div><b>{{ detail.metrics.member_count }}</b><span>成员</span></div><div><b>{{ detail.metrics.activity_count }}</b><span>活动</span></div><div><b>{{ detail.metrics.participation_count }}</b><span>参与人次</span></div><div><b>{{ detail.metrics.attendance_rate ?? '—' }}%</b><span>到场率</span></div></section>
      <section class="drawer-section"><header><h3>成员结构</h3><span>骨干 {{ detail.metrics.core_member_count }} 人</span></header><div class="roles"><div v-for="role in detail.role_distribution" :key="role.role"><span>{{ roleLabel(role.role) }}</span><div><i :style="{width: `${Math.max(7, role.count/detail.metrics.member_count*100)}%`}"></i></div><b>{{ role.count }}</b></div></div></section>
      <section class="drawer-section"><header><h3>近期活动</h3><span>{{ detail.recent_activities.length }} 条</span></header><div class="activities"><div v-for="item in detail.recent_activities" :key="item.id"><time>{{ formatDate(item.start_time).slice(5) }}</time><div><b>{{ item.title }}</b><small>{{ item.venue_name }} · {{ item.category_name }}</small></div><span>{{ item.attendance }}/{{ item.registrations }}</span></div></div></section>
      <section class="drawer-section"><header><h3>活跃成员</h3><span>按角色与参与排序</span></header><div class="members"><div v-for="item in detail.active_members" :key="item.id"><i>{{ item.name.slice(-1) }}</i><div><b>{{ item.name }}</b><small>{{ item.college_name }} · {{ roleLabel(item.role) }}</small></div><span>{{ item.participations }} 次</span></div></div></section>
    </template></aside></div>
  </div>
</template>

<style scoped>
.workspace{min-height:100vh;background:#eef3f2;color:#173237}.sidebar{position:fixed;inset:0 auto 0 0;width:232px;display:flex;flex-direction:column;padding:28px 20px;background:#103f40;color:#eaf6f3}.brand{display:flex;align-items:center;gap:12px;padding:0 8px 28px;border-bottom:1px solid rgba(255,255,255,.12)}.brand-seal{display:grid;place-items:center;width:38px;height:38px;border:1px solid #8ab3af;border-radius:50%;font:22px Georgia}.brand strong,.brand small{display:block}.brand strong{letter-spacing:.14em}.brand small{margin-top:3px;color:#a7cfca;font-size:10px}.sidebar nav{display:grid;gap:7px;margin-top:30px}.nav-item{display:flex;align-items:center;gap:13px;border-radius:7px;padding:12px 14px;color:#b7d3d0;text-decoration:none;font-size:14px}.nav-item>span{width:18px}.nav-item--active,.nav-item:hover{color:#fff;background:rgba(255,255,255,.1)}.nav-item--active{box-shadow:inset 3px 0 #e1a354}.sidebar-foot{display:flex;align-items:center;gap:10px;margin-top:auto;padding:16px 8px 0;border-top:1px solid rgba(255,255,255,.12)}.sidebar-foot i{width:8px;height:8px;border-radius:50%;background:#75c9a6}.sidebar-foot strong,.sidebar-foot small{display:block;font-size:11px}.sidebar-foot small{margin-top:3px;color:#82b5af}.main{margin-left:232px;padding:0 34px 48px}.topbar{display:flex;align-items:center;justify-content:space-between;min-height:96px}.topbar p{margin:0 0 6px;color:#7b8e8d;font-size:12px}.topbar h1{margin:0;font:600 28px STZhongsong,"Songti SC",serif}.top-meta{display:flex;align-items:center;gap:16px;color:#718684;font-size:11px}.top-meta b{display:grid;place-items:center;width:38px;height:38px;border-radius:50%;color:#fff;background:#bd7f34}.intro{display:flex;align-items:center;justify-content:space-between;min-height:150px;border:1px solid #d7e0de;border-radius:9px;padding:25px 34px;background:#fff}.intro small,.panel-head small{color:#bd7f34;font-size:10px;font-weight:700;letter-spacing:.13em}.intro h2{margin:9px 0 7px;font:600 25px STZhongsong,"Songti SC",serif}.intro p{margin:0;color:#718482;font-size:13px}.intro-total{min-width:180px;border-left:1px solid #dce5e3;padding-left:32px}.intro-total strong,.intro-total span{display:block}.intro-total strong{font:36px Bahnschrift}.intro-total span{color:#899b99;font-size:11px}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:16px 0}.cards article{display:flex;align-items:center;gap:14px;border:1px solid #d7e0de;border-radius:8px;padding:17px;background:#fff}.cards article>i{display:grid;place-items:center;width:38px;height:38px;border-radius:50%;color:#17615d;background:#e5f1ef;font:normal 16px STZhongsong}.cards span,.cards strong,.cards small{display:block}.cards span{color:#718482;font-size:11px}.cards strong{margin:3px 0;font:23px Bahnschrift}.cards small{color:#9aa8a7;font-size:9px}.panel{border:1px solid #d7e0de;border-radius:9px;padding:22px;background:#fff}.panel-head{display:flex;justify-content:space-between}.panel-head h3{margin:5px 0 0;font-size:18px}.panel-head>span{color:#8a9a98;font-size:11px}.filters{display:grid;grid-template-columns:1.4fr repeat(3,.75fr) auto;gap:9px;margin:20px 0 15px}.filters label{position:relative}.filters label i{position:absolute;left:12px;top:8px;color:#78908e;font-style:normal}.filters input,.filters select{width:100%;height:38px;border:1px solid #d3dddb;border-radius:6px;padding:0 10px;color:#344e4f;background:#f9fbfa}.filters input{padding-left:35px}.filters button,.pager button,td button{border:1px solid #bdcbc8;border-radius:5px;color:#17615d;background:#fff;cursor:pointer}.filters>button{padding:0 15px}.table-wrap{overflow-x:auto;border-top:1px solid #e3e9e8}.faded{opacity:.5}table{width:100%;border-collapse:collapse;white-space:nowrap}th{height:42px;color:#899a98;font-size:10px;text-align:left}td{height:62px;border-top:1px solid #edf1f0;color:#627674;font-size:11px}tbody tr{cursor:pointer}tbody tr:hover{background:#f4f9f8}.club-name{display:flex;align-items:center;gap:10px}.club-name>i{display:grid;place-items:center;width:34px;height:34px;border-radius:7px;color:#fff;background:#397c77;font:normal 15px STZhongsong}.club-name strong,.club-name small,td>strong,td>small{display:block}.club-name strong,td>strong{color:#294746}.club-name small,td>small{margin-top:4px;color:#90a09e;font-size:9px}td>b{font:16px Bahnschrift;color:#294746}.accent{color:#b97428}td button{padding:6px 9px}.pager{display:flex;justify-content:space-between;border-top:1px solid #e6ecea;padding-top:15px;color:#869694;font-size:10px}.pager div{display:flex;gap:5px}.pager button{height:30px;padding:0 11px}.pager b{display:grid;place-items:center;width:30px;border-radius:5px;color:#fff;background:#17615d}.error{padding:30px;color:#925e28}.mask{position:fixed;inset:0;z-index:30;background:rgba(11,42,42,.38);backdrop-filter:blur(2px)}.drawer{position:absolute;inset:0 0 0 auto;width:min(560px,100%);overflow-y:auto;padding:34px;background:#f8fbfa;box-shadow:-18px 0 50px rgba(10,45,44,.14)}.close{position:absolute;right:22px;top:18px;border:0;color:#718482;background:none;font-size:27px}.loading{display:grid;place-items:center;height:60vh}.profile{display:flex;align-items:center;gap:16px;border-bottom:1px solid #dbe4e2;padding:14px 0 23px}.profile>i{display:grid;place-items:center;width:65px;height:65px;border-radius:12px;color:#fff;background:#17615d;font:normal 26px STZhongsong}.profile small{color:#b5752d;font-size:9px}.profile h2{margin:5px 0 3px;font:600 25px STZhongsong}.profile p,.description{margin:0;color:#768987;font-size:11px}.description{padding:16px 2px;line-height:1.7}.facts{display:grid;grid-template-columns:1fr 1fr;gap:1px;margin:0 0 16px;border:1px solid #dce5e3;background:#dce5e3}.facts div{padding:11px 13px;background:#fff}.facts dt{color:#92a19f;font-size:9px}.facts dd{margin:4px 0 0;font-size:11px}.metrics{display:grid;grid-template-columns:repeat(4,1fr);padding:16px 8px;border-radius:7px;color:#fff;background:#174f4d}.metrics div{text-align:center}.metrics div+div{border-left:1px solid rgba(255,255,255,.15)}.metrics b,.metrics span{display:block}.metrics b{font:20px Bahnschrift}.metrics span{margin-top:4px;color:#acd0cb;font-size:9px}.drawer-section{margin-top:24px}.drawer-section>header{display:flex;justify-content:space-between;border-bottom:1px solid #dae4e2;padding-bottom:9px}.drawer-section h3{margin:0;font-size:14px}.drawer-section header span{color:#8d9d9b;font-size:9px}.roles>div{display:grid;grid-template-columns:65px 1fr 28px;align-items:center;gap:10px;padding:9px 0;font-size:10px}.roles>div>div{height:6px;border-radius:3px;background:#e0e9e7}.roles i{display:block;height:100%;border-radius:3px;background:#4c988e}.activities>div,.members>div{display:flex;align-items:center;gap:10px;border-bottom:1px solid #e5ebe9;padding:10px 2px}.activities time{width:45px;color:#a46c2c;font:10px Bahnschrift}.activities div>div,.members div>div{min-width:0;flex:1}.activities b,.activities small,.members b,.members small{display:block}.activities b,.members b{overflow:hidden;color:#344e4d;font-size:11px;text-overflow:ellipsis;white-space:nowrap}.activities small,.members small{margin-top:3px;color:#91a09e;font-size:9px}.activities>div>span,.members>div>span{color:#3b7771;font-size:9px}.members>div>i{display:grid;place-items:center;width:28px;height:28px;border-radius:50%;color:#fff;background:#529188;font-style:normal;font-size:10px}@media(max-width:1100px){.cards{grid-template-columns:1fr 1fr}.filters{grid-template-columns:1fr 1fr 1fr}}@media(max-width:760px){.sidebar{position:static;width:auto}.sidebar nav,.sidebar-foot{display:none}.main{margin-left:0;padding:0 14px 30px}.intro-total{display:none}.cards{grid-template-columns:1fr 1fr}.filters{grid-template-columns:1fr}}@media(max-width:440px){.cards{grid-template-columns:1fr}}
</style>
