<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import { http } from '@/api/http'
import type { StudentDetail, StudentListResponse } from '@/types/student'

const data = ref<StudentListResponse | null>(null)
const detail = ref<StudentDetail | null>(null)
const loading = ref(true)
const detailLoading = ref(false)
const error = ref('')
const page = ref(1)
const pageSize = 20
const search = ref('')
const collegeId = ref('')
const majorId = ref('')
const gradeNo = ref('')
const status = ref('active')
let searchTimer: ReturnType<typeof setTimeout> | undefined

const numberFormatter = new Intl.NumberFormat('zh-CN')
const filteredMajors = computed(() => {
  const majors = data.value?.options.majors ?? []
  return collegeId.value ? majors.filter((major) => major.college_id === Number(collegeId.value)) : majors
})
const totalPages = computed(() => Math.max(1, Math.ceil((data.value?.total ?? 0) / pageSize)))
const summaryCards = computed(() => [
  { label: '在校学生', value: data.value?.summary.total_students ?? 0, note: '当前有效学生档案', icon: '人' },
  { label: '覆盖学院', value: data.value?.summary.college_count ?? 0, note: '专业分布完整', icon: '院' },
  { label: '参与过活动', value: data.value?.summary.participating_students ?? 0, note: '有实际签到记录', icon: '参' },
  { label: '加入社团', value: data.value?.summary.club_members ?? 0, note: '当前活跃成员', icon: '社' },
])

async function loadStudents(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    const response = await http.get<StudentListResponse>('/students', {
      params: {
        page: page.value,
        page_size: pageSize,
        search: search.value || undefined,
        college_id: collegeId.value || undefined,
        major_id: majorId.value || undefined,
        grade_no: gradeNo.value || undefined,
        status: status.value || undefined,
      },
    })
    data.value = response.data
  } catch {
    error.value = '学生数据加载失败，请检查 FastAPI 与 MySQL 服务。'
  } finally {
    loading.value = false
  }
}

async function openDetail(studentId: number): Promise<void> {
  detailLoading.value = true
  detail.value = null
  try {
    detail.value = (await http.get<StudentDetail>(`/students/${studentId}`)).data
  } finally {
    detailLoading.value = false
  }
}

function resetFilters(): void {
  search.value = ''
  collegeId.value = ''
  majorId.value = ''
  gradeNo.value = ''
  status.value = 'active'
  page.value = 1
  void loadStudents()
}

function changePage(nextPage: number): void {
  if (nextPage < 1 || nextPage > totalPages.value || nextPage === page.value) return
  page.value = nextPage
  void loadStudents()
}

function formatDate(value: string | null): string {
  if (!value) return '暂无参与'
  return new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date(value))
}

function roleLabel(role: string): string {
  return { leader: '负责人', core: '骨干', member: '成员' }[role] ?? role
}

watch(collegeId, () => {
  majorId.value = ''
})
watch([collegeId, majorId, gradeNo, status], () => {
  page.value = 1
  void loadStudents()
})
watch(search, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    void loadStudents()
  }, 320)
})

onMounted(loadStudents)
</script>

<template>
  <div class="workspace">
    <aside class="sidebar">
      <div class="brand"><span class="brand-seal">S</span><div><strong>SZUT</strong><small>校园活动数据中心</small></div></div>
      <nav aria-label="主导航">
        <RouterLink class="nav-item" to="/"><span>▦</span>数据总览</RouterLink>
        <RouterLink class="nav-item nav-item--active" to="/students"><span>◎</span>学生管理</RouterLink>
        <RouterLink class="nav-item" to="/clubs"><span>◇</span>社团管理</RouterLink>
        <span class="nav-item nav-item--disabled"><span>□</span>活动管理</span>
        <span class="nav-item nav-item--disabled"><span>⌁</span>统计分析</span>
        <span class="nav-item nav-item--disabled"><span>✦</span>智能分析</span>
      </nav>
      <div class="sidebar-foot"><span class="online-dot"></span><div><strong>系统运行正常</strong><small>学生档案已连接</small></div></div>
    </aside>

    <main class="main-content">
      <header class="topbar">
        <div><p>校园基础数据 / 学生档案</p><h1>学生管理</h1></div>
        <div class="header-meta"><span>DATASET</span><strong>2025—2026</strong><div class="avatar">管</div></div>
      </header>

      <section class="page-intro">
        <div><span class="eyebrow">STUDENT DIRECTORY</span><h2>从学生档案，看见校园参与轨迹</h2><p>按学院、专业和年级快速检索，点击名单可查看社团归属与活动参与记录。</p></div>
        <div class="intro-mark"><strong>{{ numberFormatter.format(data?.total ?? 0) }}</strong><span>当前筛选结果</span></div>
      </section>

      <section class="summary-grid" aria-label="学生数据摘要">
        <article v-for="card in summaryCards" :key="card.label" class="summary-card"><span class="summary-icon">{{ card.icon }}</span><div><small>{{ card.label }}</small><strong>{{ numberFormatter.format(card.value) }}</strong><em>{{ card.note }}</em></div></article>
      </section>

      <section class="directory-panel">
        <header class="panel-header"><div><span class="section-tag">档案检索</span><h3>学生名单</h3></div><p>共 {{ numberFormatter.format(data?.total ?? 0) }} 条记录</p></header>
        <div class="filters">
          <label class="search-box"><span>⌕</span><input v-model.trim="search" type="search" placeholder="输入姓名或学号" /></label>
          <select v-model="collegeId" aria-label="学院"><option value="">全部学院</option><option v-for="college in data?.options.colleges" :key="college.id" :value="String(college.id)">{{ college.name }}</option></select>
          <select v-model="majorId" aria-label="专业"><option value="">全部专业</option><option v-for="major in filteredMajors" :key="major.id" :value="String(major.id)">{{ major.name }}</option></select>
          <select v-model="gradeNo" aria-label="年级"><option value="">全部年级</option><option value="1">一年级</option><option value="2">二年级</option><option value="3">三年级</option><option value="4">四年级</option></select>
          <select v-model="status" aria-label="状态"><option value="">全部状态</option><option value="active">在校</option><option value="graduated">已毕业</option><option value="suspended">暂停</option></select>
          <button class="reset-button" type="button" @click="resetFilters">重置</button>
        </div>

        <div v-if="error" class="message message--error">{{ error }}<button type="button" @click="loadStudents">重新加载</button></div>
        <div v-else class="table-wrap" :class="{ 'is-loading': loading }">
          <table>
            <thead><tr><th>学生</th><th>学院 / 专业</th><th>年级班级</th><th>社团</th><th>实际参与</th><th>最近活动</th><th></th></tr></thead>
            <tbody>
              <tr v-for="student in data?.items" :key="student.id" @click="openDetail(student.id)">
                <td><div class="student-cell"><span class="student-avatar">{{ student.name.slice(-1) }}</span><div><strong>{{ student.name }}</strong><small>{{ student.student_no }} · {{ student.gender }}</small></div></div></td>
                <td><strong class="cell-primary">{{ student.college_name }}</strong><small class="cell-secondary">{{ student.major_name }}</small></td>
                <td><span class="grade-badge">{{ student.grade_no }} 年级</span><small class="cell-secondary">{{ student.class_name }}</small></td>
                <td><strong class="data-number">{{ student.club_count }}</strong><small class="unit"> 个</small></td>
                <td><strong class="data-number data-number--accent">{{ student.participation_count }}</strong><small class="unit"> 次</small></td>
                <td>{{ formatDate(student.last_activity_at) }}</td>
                <td><button class="detail-button" type="button" @click.stop="openDetail(student.id)">查看档案</button></td>
              </tr>
            </tbody>
          </table>
          <div v-if="!loading && !data?.items.length" class="empty-state">没有符合当前条件的学生，调整筛选后重试。</div>
        </div>

        <footer class="pagination"><span>第 {{ page }} / {{ totalPages }} 页</span><div><button type="button" :disabled="page === 1" @click="changePage(page - 1)">上一页</button><button class="page-current" type="button">{{ page }}</button><button type="button" :disabled="page === totalPages" @click="changePage(page + 1)">下一页</button></div></footer>
      </section>
    </main>

    <div v-if="detailLoading || detail" class="drawer-layer" @click.self="detail = null">
      <aside class="detail-drawer" aria-label="学生参与档案">
        <button class="drawer-close" type="button" aria-label="关闭" @click="detail = null">×</button>
        <div v-if="detailLoading" class="drawer-loading">正在读取学生档案…</div>
        <template v-else-if="detail">
          <header class="profile-head"><span class="profile-avatar">{{ detail.name.slice(-1) }}</span><div><span class="section-tag">学生参与档案</span><h2>{{ detail.name }}</h2><p>{{ detail.student_no }} · {{ detail.college_name }}</p></div></header>
          <dl class="profile-facts"><div><dt>专业</dt><dd>{{ detail.major_name }}</dd></div><div><dt>班级</dt><dd>{{ detail.class_name }}</dd></div><div><dt>年级</dt><dd>{{ detail.grade_no }} 年级</dd></div><div><dt>状态</dt><dd>在校</dd></div></dl>
          <section class="detail-stats"><div><strong>{{ detail.participation_summary.club_count }}</strong><span>加入社团</span></div><div><strong>{{ detail.participation_summary.registration_count }}</strong><span>有效报名</span></div><div><strong>{{ detail.participation_summary.participation_count }}</strong><span>实际参与</span></div><div><strong>{{ detail.participation_summary.attendance_rate ?? '—' }}%</strong><span>到场率</span></div></section>
          <section class="drawer-section"><header><h3>所属社团</h3><span>{{ detail.clubs.length }} 个</span></header><div v-if="detail.clubs.length" class="club-list"><div v-for="club in detail.clubs" :key="club.id"><span class="club-dot"></span><div><strong>{{ club.name }}</strong><small>{{ club.category_name }} · {{ roleLabel(club.role) }}</small></div></div></div><p v-else class="empty-copy">该学生暂未加入社团。</p></section>
          <section class="drawer-section"><header><h3>最近参与活动</h3><span>近 {{ detail.recent_activities.length }} 条</span></header><div class="activity-list"><div v-for="activity in detail.recent_activities" :key="activity.id"><time>{{ formatDate(activity.start_time).slice(5) }}</time><div><strong>{{ activity.title }}</strong><small>{{ activity.club_name }} · {{ activity.category_name }}</small></div><span :class="`attendance attendance--${activity.attendance_status}`">{{ activity.attendance_status === 'late' ? '迟到' : activity.attendance_status === 'present' ? '到场' : '缺席' }}</span></div></div></section>
        </template>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.workspace{min-height:100vh;background:#eef3f2;color:#173237}.sidebar{position:fixed;inset:0 auto 0 0;z-index:10;width:232px;display:flex;flex-direction:column;padding:28px 20px;background:#103f40;color:#eaf6f3}.brand{display:flex;align-items:center;gap:12px;padding:0 8px 28px;border-bottom:1px solid rgba(255,255,255,.12)}.brand-seal{display:grid;place-items:center;width:38px;height:38px;border:1px solid rgba(255,255,255,.55);border-radius:50%;font-family:Georgia,serif;font-size:22px}.brand strong,.brand small{display:block}.brand strong{letter-spacing:.14em}.brand small{margin-top:3px;color:#a7cfca;font-size:10px;letter-spacing:.08em}.sidebar nav{display:grid;gap:7px;margin-top:30px}.nav-item{display:flex;align-items:center;gap:13px;border-radius:7px;padding:12px 14px;color:#b7d3d0;text-decoration:none;font-size:14px}.nav-item span{width:18px;font-size:17px}.nav-item:hover,.nav-item--active{color:#fff;background:rgba(255,255,255,.1)}.nav-item--active{box-shadow:inset 3px 0 #e1a354}.nav-item--disabled{cursor:default}.sidebar-foot{display:flex;align-items:center;gap:10px;margin-top:auto;padding:16px 8px 0;border-top:1px solid rgba(255,255,255,.12)}.sidebar-foot strong,.sidebar-foot small{display:block;font-size:11px}.sidebar-foot small{margin-top:3px;color:#82b5af}.online-dot{width:8px;height:8px;border-radius:50%;background:#75c9a6;box-shadow:0 0 0 4px rgba(117,201,166,.12)}.main-content{min-width:0;margin-left:232px;padding:0 34px 48px}.topbar{display:flex;align-items:center;justify-content:space-between;min-height:96px}.topbar p{margin:0 0 6px;color:#7b8e8d;font-size:12px;letter-spacing:.08em}.topbar h1{margin:0;font-family:STZhongsong,"Songti SC",serif;font-size:28px;font-weight:600}.header-meta{display:flex;align-items:center;gap:12px;color:#78908e}.header-meta>span{font-family:Bahnschrift,sans-serif;font-size:9px;letter-spacing:.15em}.header-meta>strong{font-family:Bahnschrift,sans-serif;font-size:12px}.avatar{display:grid;place-items:center;width:38px;height:38px;margin-left:8px;border-radius:50%;color:#fff;background:#bd7f34}.page-intro{display:flex;align-items:center;justify-content:space-between;min-height:152px;border-radius:9px;padding:26px 34px;background:#fff;border:1px solid #d7e0de}.eyebrow,.section-tag{color:#bd7f34;font-size:10px;font-weight:700;letter-spacing:.13em}.page-intro h2{margin:9px 0 7px;font-family:STZhongsong,"Songti SC",serif;font-size:25px;font-weight:600}.page-intro p{margin:0;color:#718482;font-size:13px}.intro-mark{min-width:180px;border-left:1px solid #dce5e3;padding-left:32px}.intro-mark strong,.intro-mark span{display:block}.intro-mark strong{font-family:Bahnschrift,sans-serif;font-size:36px}.intro-mark span{margin-top:3px;color:#899b99;font-size:11px}.summary-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:16px 0}.summary-card{display:flex;align-items:center;gap:15px;border:1px solid #d7e0de;border-radius:8px;padding:17px 18px;background:#fff}.summary-icon{display:grid;place-items:center;width:38px;height:38px;border-radius:50%;color:#0b625f;background:#e5f1ef;font-family:STZhongsong,serif}.summary-card small,.summary-card strong,.summary-card em{display:block}.summary-card small{color:#718482;font-size:11px}.summary-card strong{margin:3px 0 1px;font-family:Bahnschrift,sans-serif;font-size:23px}.summary-card em{color:#9aa8a7;font-size:9px;font-style:normal}.directory-panel{border:1px solid #d7e0de;border-radius:9px;padding:22px;background:#fff}.panel-header{display:flex;align-items:flex-start;justify-content:space-between}.panel-header h3{margin:5px 0 0;font-size:18px}.panel-header p{margin:7px 0 0;color:#8a9a98;font-size:11px}.filters{display:grid;grid-template-columns:minmax(190px,1.4fr) repeat(4,minmax(118px,.8fr)) auto;gap:9px;margin:20px 0 15px}.filters input,.filters select{width:100%;height:38px;border:1px solid #d3dddb;border-radius:6px;padding:0 10px;color:#344e4f;background:#f9fbfa;font-size:12px}.search-box{position:relative}.search-box span{position:absolute;left:12px;top:8px;color:#79908e;font-size:17px}.search-box input{padding-left:36px}.reset-button{height:38px;border:1px solid #bdc9c7;border-radius:6px;padding:0 14px;color:#5e7472;background:#fff;cursor:pointer}.table-wrap{position:relative;overflow-x:auto;min-height:280px;border-top:1px solid #e3e9e8}.table-wrap.is-loading{opacity:.48}.table-wrap.is-loading:after{position:absolute;inset:70px 0 auto;content:"数据加载中…";color:#687c7a;text-align:center}table{width:100%;border-collapse:collapse;white-space:nowrap}th{height:42px;color:#899a98;font-size:10px;font-weight:600;text-align:left}td{height:62px;border-top:1px solid #edf1f0;color:#627674;font-size:11px}tbody tr{cursor:pointer;transition:background-color .14s}tbody tr:hover{background:#f4f9f8}.student-cell{display:flex;align-items:center;gap:10px}.student-avatar{display:grid;place-items:center;width:34px;height:34px;border-radius:50%;color:#fff;background:#397c77}.student-cell strong,.student-cell small,.cell-primary,.cell-secondary{display:block}.student-cell strong,.cell-primary{color:#264243;font-size:12px}.student-cell small,.cell-secondary{margin-top:4px;color:#8c9c9a;font-size:9px}.grade-badge{display:inline-block;border-radius:9px;padding:3px 7px;color:#3d716c;background:#e9f3f1;font-size:9px}.data-number{color:#294847;font-family:Bahnschrift,sans-serif;font-size:16px}.data-number--accent{color:#b97428}.unit{color:#9aa7a6}.detail-button{border:1px solid #b7cbc7;border-radius:5px;padding:6px 9px;color:#17615d;background:#fff;cursor:pointer;font-size:10px}.empty-state{padding:60px;text-align:center;color:#8a9a98}.message{margin-top:15px;border-radius:6px;padding:14px;font-size:12px}.message--error{color:#85511e;background:#fff4e8}.message button{margin-left:12px;border:0;color:#fff;background:#a56b2a}.pagination{display:flex;align-items:center;justify-content:space-between;border-top:1px solid #e6ecea;padding-top:15px;color:#869694;font-size:10px}.pagination div{display:flex;gap:5px}.pagination button{height:30px;border:1px solid #ccd8d6;border-radius:5px;padding:0 11px;color:#536b69;background:#fff}.pagination button:disabled{opacity:.4}.pagination .page-current{color:#fff;background:#17615d}.drawer-layer{position:fixed;inset:0;z-index:30;background:rgba(11,42,42,.38);backdrop-filter:blur(2px)}.detail-drawer{position:absolute;inset:0 0 0 auto;width:min(520px,100%);overflow-y:auto;padding:34px;background:#f8fbfa;box-shadow:-18px 0 50px rgba(10,45,44,.14)}.drawer-close{position:absolute;top:20px;right:23px;border:0;color:#6f8280;background:transparent;font-size:27px;cursor:pointer}.drawer-loading{display:grid;place-items:center;height:60vh;color:#718482}.profile-head{display:flex;align-items:center;gap:17px;border-bottom:1px solid #dbe4e2;padding:16px 0 24px}.profile-avatar{display:grid;place-items:center;width:64px;height:64px;border-radius:50%;color:#fff;background:#17615d;font-family:STZhongsong,serif;font-size:25px}.profile-head h2{margin:5px 0 3px;font-family:STZhongsong,serif;font-size:25px}.profile-head p{margin:0;color:#768987;font-size:11px}.profile-facts{display:grid;grid-template-columns:1fr 1fr;gap:1px;margin:18px 0;background:#dce5e3;border:1px solid #dce5e3}.profile-facts div{padding:12px 14px;background:#fff}.profile-facts dt{color:#91a09e;font-size:9px}.profile-facts dd{margin:4px 0 0;color:#365150;font-size:11px}.detail-stats{display:grid;grid-template-columns:repeat(4,1fr);border-radius:7px;padding:16px 8px;color:#eaf6f3;background:#174f4d}.detail-stats div{text-align:center}.detail-stats div+div{border-left:1px solid rgba(255,255,255,.15)}.detail-stats strong,.detail-stats span{display:block}.detail-stats strong{font-family:Bahnschrift,sans-serif;font-size:20px}.detail-stats span{margin-top:4px;color:#acd0cb;font-size:9px}.drawer-section{margin-top:25px}.drawer-section>header{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #dae4e2;padding-bottom:10px}.drawer-section h3{margin:0;font-size:14px}.drawer-section header span{color:#8d9d9b;font-size:9px}.club-list>div,.activity-list>div{display:flex;align-items:center;gap:10px;border-bottom:1px solid #e5ebe9;padding:11px 2px}.club-dot{width:7px;height:7px;border:2px solid #359186;border-radius:50%}.club-list strong,.club-list small,.activity-list strong,.activity-list small{display:block}.club-list strong,.activity-list strong{color:#344e4d;font-size:11px}.club-list small,.activity-list small{margin-top:3px;color:#91a09e;font-size:9px}.activity-list time{width:42px;color:#a46c2c;font-family:Bahnschrift,sans-serif;font-size:10px}.activity-list>div>div{min-width:0;flex:1}.activity-list strong{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.attendance{border-radius:8px;padding:3px 7px;font-size:8px}.attendance--present{color:#1b6f65;background:#e4f3ef}.attendance--late{color:#9a651f;background:#fff0dc}.attendance--absent{color:#8b5f5f;background:#f5e7e7}.empty-copy{color:#8e9e9c;font-size:11px}@media(max-width:1180px){.summary-grid{grid-template-columns:1fr 1fr}.filters{grid-template-columns:1fr 1fr 1fr}.header-meta>span,.header-meta>strong{display:none}}@media(max-width:760px){.sidebar{position:static;width:auto}.sidebar nav,.sidebar-foot{display:none}.main-content{margin-left:0;padding:0 14px 30px}.page-intro{padding:24px}.intro-mark{display:none}.summary-grid{grid-template-columns:1fr 1fr}.filters{grid-template-columns:1fr}.directory-panel{padding:16px}.topbar{min-height:80px}}@media(max-width:440px){.summary-grid{grid-template-columns:1fr}.detail-stats{grid-template-columns:1fr 1fr;gap:12px}.detail-stats div+div{border-left:0}}
</style>
