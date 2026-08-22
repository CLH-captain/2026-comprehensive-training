<script setup lang="ts">
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { computed, onMounted, ref } from 'vue'
import VChart from 'vue-echarts'

import { http } from '@/api/http'
import type { DashboardResponse } from '@/types/dashboard'

use([CanvasRenderer, LineChart, BarChart, PieChart, GridComponent, TooltipComponent, LegendComponent])

const dashboard = ref<DashboardResponse | null>(null)
const loading = ref(true)
const error = ref('')
const termId = ref('')
const campusId = ref('')

const numberFormatter = new Intl.NumberFormat('zh-CN')

async function loadDashboard(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    const response = await http.get<DashboardResponse>('/statistics/dashboard', {
      params: {
        term_id: termId.value || undefined,
        campus_id: campusId.value || undefined,
      },
    })
    dashboard.value = response.data
  } catch {
    error.value = '统计服务暂时不可用，请确认 FastAPI 与 MySQL 已启动。'
  } finally {
    loading.value = false
  }
}

const overviewCards = computed(() => {
  const value = dashboard.value?.overview
  return [
    { label: '正常运行社团', value: value ? numberFormatter.format(value.active_clubs) : '—', unit: '个', tone: 'lake' },
    { label: '已开展活动', value: value ? numberFormatter.format(value.completed_activities) : '—', unit: '场', tone: 'jade' },
    { label: '活动参与人次', value: value ? numberFormatter.format(value.participations) : '—', unit: '人次', tone: 'amber' },
    { label: '活跃学生', value: value ? numberFormatter.format(value.active_students) : '—', unit: '人', tone: 'blue' },
  ]
})

const trendOption = computed(() => ({
  color: ['#0b625f', '#d08a36'],
  tooltip: { trigger: 'axis' },
  legend: { data: ['参与人次', '活动数'], right: 4, top: 0, textStyle: { color: '#607271' } },
  grid: { left: 48, right: 48, top: 44, bottom: 32 },
  xAxis: { type: 'category', data: dashboard.value?.monthly_trend.map((item) => item.month.slice(5) + '月') ?? [], axisLine: { lineStyle: { color: '#ccd8d6' } }, axisTick: { show: false } },
  yAxis: [
    { type: 'value', splitLine: { lineStyle: { color: '#edf2f1' } } },
    { type: 'value', splitLine: { show: false } },
  ],
  series: [
    { name: '参与人次', type: 'line', smooth: 0.28, symbolSize: 7, data: dashboard.value?.monthly_trend.map((item) => item.participations) ?? [], areaStyle: { color: 'rgba(11,98,95,.08)' } },
    { name: '活动数', type: 'bar', yAxisIndex: 1, barMaxWidth: 18, data: dashboard.value?.monthly_trend.map((item) => item.activities) ?? [], itemStyle: { borderRadius: [4, 4, 0, 0] } },
  ],
}))

const clubOption = computed(() => ({
  color: ['#378d82'],
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  grid: { left: 114, right: 20, top: 12, bottom: 24 },
  xAxis: { type: 'value', splitLine: { lineStyle: { color: '#edf2f1' } } },
  yAxis: { type: 'category', inverse: true, data: dashboard.value?.club_ranking.map((item) => item.name) ?? [], axisTick: { show: false }, axisLine: { show: false } },
  series: [{ type: 'bar', data: dashboard.value?.club_ranking.map((item) => item.participations) ?? [], barWidth: 13, itemStyle: { borderRadius: [0, 5, 5, 0] } }],
}))

const categoryOption = computed(() => ({
  color: ['#0b625f', '#378d82', '#65a89e', '#d08a36', '#e5aa64', '#527b92', '#8ba9b5'],
  tooltip: { trigger: 'item', formatter: '{b}<br/>{c} 人次 · {d}%' },
  legend: { bottom: 0, left: 'center', itemWidth: 9, itemHeight: 9, textStyle: { color: '#637777', fontSize: 11 } },
  series: [{ type: 'pie', radius: ['47%', '70%'], center: ['50%', '43%'], label: { show: false }, itemStyle: { borderColor: '#fff', borderWidth: 3 }, data: dashboard.value?.category_distribution.map((item) => ({ name: item.name, value: item.participations })) ?? [] }],
}))

onMounted(loadDashboard)
</script>

<template>
  <div class="workspace">
    <aside class="sidebar">
      <div class="brand"><span class="brand-seal">S</span><div><strong>SZUT</strong><small>校园活动数据中心</small></div></div>
      <nav aria-label="主导航">
        <a class="nav-item nav-item--active" href="#"><span>▦</span>数据总览</a>
        <a class="nav-item" href="/students"><span>◎</span>学生管理</a>
        <a class="nav-item" href="/clubs"><span>◇</span>社团管理</a>
        <a class="nav-item" href="/activities"><span>□</span>活动管理</a>
        <a class="nav-item" href="#analytics"><span>⌁</span>统计分析</a>
        <a class="nav-item" href="#agent"><span>✦</span>智能分析</a>
      </nav>
      <div class="sidebar-foot"><span class="online-dot"></span><div><strong>系统运行正常</strong><small>MySQL 数据已连接</small></div></div>
    </aside>

    <main class="main-content">
      <header class="topbar">
        <div><p>校园社团活动参与统计</p><h1>数据总览</h1></div>
        <div class="top-actions">
          <label>学期<select v-model="termId" @change="loadDashboard"><option value="">2025—2026 全学年</option><option v-for="term in dashboard?.contexts.terms" :key="term.id" :value="String(term.id)">{{ term.name }}</option></select></label>
          <label>校区<select v-model="campusId" @change="loadDashboard"><option value="">全部校区</option><option v-for="campus in dashboard?.contexts.campuses" :key="campus.id" :value="String(campus.id)">{{ campus.name }}</option></select></label>
          <div class="avatar">管</div>
        </div>
      </header>

      <section class="hero">
        <div><span class="hero-tag">2025—2026 学年</span><h2>看见校园活力，理解每一次参与</h2><p>数据来自本地 MySQL 仿真数据集，统计口径在 Dashboard、API 与后续 Agent 间保持一致。</p></div>
        <div class="hero-rate"><span>综合到场率</span><strong>{{ dashboard?.overview.attendance_rate ?? '—' }}<small>%</small></strong><em>报名 → 实际参与</em></div>
      </section>

      <div v-if="error" class="error-state">{{ error }}<button type="button" @click="loadDashboard">重新加载</button></div>
      <template v-else>
        <section class="metrics" aria-label="核心指标">
          <article v-for="card in overviewCards" :key="card.label" class="metric-card" :class="`metric-card--${card.tone}`">
            <span>{{ card.label }}</span><div><strong>{{ card.value }}</strong><small>{{ card.unit }}</small></div><em>{{ loading ? '数据加载中' : '来自当前筛选范围' }}</em>
          </article>
        </section>

        <section class="dashboard-grid">
          <article class="panel panel--wide"><header><div><span>趋势观察</span><h3>月度活动与参与趋势</h3></div><small>单位：场 / 人次</small></header><VChart class="chart chart--trend" :option="trendOption" autoresize /></article>
          <article class="panel"><header><div><span>结构分布</span><h3>活动类别参与分布</h3></div></header><VChart class="chart" :option="categoryOption" autoresize /></article>
          <article class="panel"><header><div><span>社团活力</span><h3>参与人次 TOP 8</h3></div></header><VChart class="chart chart--rank" :option="clubOption" autoresize /></article>
          <article class="panel panel--wide"><header><div><span>热门活动</span><h3>参与人数排行榜</h3></div><small>按实际签到统计</small></header>
            <div class="activity-table"><div class="table-row table-head"><span>活动名称</span><span>举办社团</span><span>报名</span><span>到场</span><span>到场率</span></div><div v-for="activity in dashboard?.top_activities" :key="activity.id" class="table-row"><strong>{{ activity.title }}</strong><span>{{ activity.club_name }}</span><span>{{ activity.registrations }}</span><span>{{ activity.attendance }}</span><em>{{ activity.attendance_rate }}%</em></div></div>
          </article>
        </section>
      </template>
    </main>
  </div>
</template>

<style scoped>
.workspace{min-height:100vh;background:#eef3f2;color:#173237}.sidebar{position:fixed;inset:0 auto 0 0;width:232px;display:flex;flex-direction:column;padding:28px 20px;background:#103f40;color:#eaf6f3}.brand{display:flex;align-items:center;gap:12px;padding:0 8px 28px;border-bottom:1px solid rgba(255,255,255,.12)}.brand-seal{display:grid;place-items:center;width:38px;height:38px;border:1px solid rgba(255,255,255,.55);border-radius:50%;font-family:Georgia,serif;font-size:22px}.brand strong,.brand small{display:block}.brand strong{letter-spacing:.14em}.brand small{margin-top:3px;color:#a7cfca;font-size:10px;letter-spacing:.08em}.sidebar nav{display:grid;gap:7px;margin-top:30px}.nav-item{display:flex;align-items:center;gap:13px;border-radius:7px;padding:12px 14px;color:#b7d3d0;text-decoration:none;font-size:14px}.nav-item span{width:18px;font-size:17px}.nav-item:hover,.nav-item--active{color:#fff;background:rgba(255,255,255,.1)}.nav-item--active{box-shadow:inset 3px 0 #e1a354}.sidebar-foot{display:flex;align-items:center;gap:10px;margin-top:auto;padding:16px 8px 0;border-top:1px solid rgba(255,255,255,.12)}.sidebar-foot strong,.sidebar-foot small{display:block;font-size:11px}.sidebar-foot small{margin-top:3px;color:#82b5af}.online-dot{width:8px;height:8px;border-radius:50%;background:#75c9a6;box-shadow:0 0 0 4px rgba(117,201,166,.12)}.main-content{min-width:0;margin-left:232px;padding:0 34px 48px}.topbar{display:flex;align-items:center;justify-content:space-between;min-height:96px}.topbar p{margin:0 0 6px;color:#7b8e8d;font-size:12px;letter-spacing:.08em}.topbar h1{margin:0;font-family:STZhongsong,"Songti SC",serif;font-size:28px;font-weight:600}.top-actions{display:flex;align-items:flex-end;gap:12px}.top-actions label{display:grid;gap:5px;color:#738786;font-size:10px;letter-spacing:.06em}.top-actions select{min-width:150px;height:37px;border:1px solid #cbd9d6;border-radius:6px;padding:0 30px 0 11px;color:#294446;background:#fff}.avatar{display:grid;place-items:center;width:38px;height:38px;border-radius:50%;color:#fff;background:#bd7f34}.hero{position:relative;display:flex;align-items:center;justify-content:space-between;overflow:hidden;min-height:174px;border-radius:10px;padding:30px 38px;color:#fff;background:linear-gradient(105deg,#0c5d59,#1f7770)}.hero:after{position:absolute;right:16%;width:280px;height:280px;border:1px solid rgba(255,255,255,.12);border-radius:50%;box-shadow:0 0 0 48px rgba(255,255,255,.035),0 0 0 100px rgba(255,255,255,.025);content:""}.hero>div{position:relative;z-index:1}.hero-tag{color:#b7ded7;font-size:11px;letter-spacing:.12em}.hero h2{margin:10px 0 8px;font-family:STZhongsong,"Songti SC",serif;font-size:28px;font-weight:500}.hero p{max-width:650px;margin:0;color:#d5ebe7;font-size:13px;line-height:1.7}.hero-rate{min-width:185px;border-left:1px solid rgba(255,255,255,.25);padding-left:34px}.hero-rate span,.hero-rate em{display:block;color:#b9dcd7;font-size:11px;font-style:normal}.hero-rate strong{display:block;margin:4px 0;font-family:Bahnschrift,sans-serif;font-size:44px;font-weight:500}.hero-rate small{font-size:17px}.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin:18px 0}.metric-card{position:relative;overflow:hidden;border:1px solid #d7e0de;border-radius:8px;padding:20px 21px;background:#fff}.metric-card:before{position:absolute;inset:0 auto 0 0;width:3px;background:#0b625f;content:""}.metric-card--amber:before{background:#d08a36}.metric-card--blue:before{background:#527b92}.metric-card--jade:before{background:#57a091}.metric-card>span{color:#6f8382;font-size:12px}.metric-card div{margin:12px 0 5px}.metric-card strong{font-family:Bahnschrift,sans-serif;font-size:29px;font-weight:600}.metric-card small{margin-left:5px;color:#6c7e7d}.metric-card em{color:#9aa9a8;font-size:10px;font-style:normal}.dashboard-grid{display:grid;grid-template-columns:minmax(320px,.8fr) minmax(500px,1.2fr);gap:16px}.panel{min-width:0;border:1px solid #d7e0de;border-radius:8px;padding:20px;background:#fff}.panel--wide{grid-column:span 1}.panel header{display:flex;align-items:flex-start;justify-content:space-between}.panel header span{color:#bf7b2f;font-size:10px;font-weight:700;letter-spacing:.12em}.panel h3{margin:5px 0 0;font-size:16px;font-weight:600}.panel header small{color:#95a3a2;font-size:10px}.chart{height:320px}.chart--trend{height:300px}.chart--rank{height:335px}.activity-table{margin-top:19px}.table-row{display:grid;grid-template-columns:minmax(210px,2fr) minmax(110px,1fr) 62px 62px 70px;align-items:center;gap:10px;min-height:42px;border-top:1px solid #edf1f0;color:#647776;font-size:12px}.table-row strong{overflow:hidden;color:#284243;font-weight:500;text-overflow:ellipsis;white-space:nowrap}.table-row em{width:55px;border-radius:10px;padding:3px 5px;color:#187066;background:#e8f4f1;text-align:center;font-size:10px;font-style:normal}.table-head{min-height:32px;border-top:0;color:#9aa7a6;font-size:10px}.error-state{margin:18px 0;border:1px solid #e5c7a3;border-radius:8px;padding:18px;color:#7b5528;background:#fff9f1}.error-state button{margin-left:16px;border:0;color:#fff;background:#a66d2b;padding:7px 12px}@media(max-width:1100px){.metrics{grid-template-columns:repeat(2,1fr)}.dashboard-grid{grid-template-columns:1fr}.top-actions label{display:none}}@media(max-width:760px){.sidebar{position:static;width:auto;min-height:auto}.sidebar nav,.sidebar-foot{display:none}.workspace{display:block}.main-content{margin-left:0;padding:0 16px 32px}.topbar{min-height:82px}.hero{padding:26px}.hero-rate{display:none}.metrics{grid-template-columns:1fr 1fr}.activity-table{overflow-x:auto}.table-row{min-width:650px}}@media(max-width:480px){.metrics{grid-template-columns:1fr}.hero h2{font-size:23px}}
</style>
