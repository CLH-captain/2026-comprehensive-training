<script setup lang="ts">
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import VChart from 'vue-echarts'

import { http } from '@/api/http'
import type { DashboardResponse } from '@/types/dashboard'

use([CanvasRenderer, BarChart, LineChart, PieChart, GridComponent, LegendComponent, TooltipComponent])
interface RankedItem { id: number; name?: string; title?: string; participations: number; activity_score?: number }
interface DistributionItem { id: number; name: string; participations: number }
interface TrendItem { month: string; activities: number; participations: number }

const loading = ref(false)
const error = ref('')
const contexts = ref<DashboardResponse['contexts']>({ terms: [], campuses: [] })
const filters = reactive({ term_id: '', campus_id: '', date_from: '', date_to: '' })
const trends = ref<TrendItem[]>([])
const clubs = ref<RankedItem[]>([])
const activities = ref<RankedItem[]>([])
const students = ref<RankedItem[]>([])
const colleges = ref<RankedItem[]>([])
const categories = ref<DistributionItem[]>([])
const campuses = ref<DistributionItem[]>([])
const params = computed(() => Object.fromEntries(Object.entries(filters).filter(([, value]) => value)))

async function loadAnalytics(): Promise<void> {
  loading.value = true; error.value = ''
  try {
    const [dashboard, trend, club, activity, student, college, category, campus] = await Promise.all([
      http.get<DashboardResponse>('/statistics/dashboard'),
      http.get<TrendItem[]>('/statistics/trends/monthly', { params: params.value }),
      http.get<RankedItem[]>('/statistics/rankings/club', { params: { ...params.value, limit: 10 } }),
      http.get<RankedItem[]>('/statistics/rankings/activity', { params: { ...params.value, limit: 10 } }),
      http.get<RankedItem[]>('/statistics/rankings/student', { params: { ...params.value, limit: 10 } }),
      http.get<RankedItem[]>('/statistics/rankings/college', { params: { ...params.value, limit: 10 } }),
      http.get<DistributionItem[]>('/statistics/distributions/category', { params: params.value }),
      http.get<DistributionItem[]>('/statistics/distributions/campus', { params: params.value }),
    ])
    contexts.value = dashboard.data.contexts; trends.value = trend.data; clubs.value = club.data
    activities.value = activity.data; students.value = student.data; colleges.value = college.data
    categories.value = category.data; campuses.value = campus.data
  } catch { error.value = '统计分析加载失败，请检查筛选范围或后端服务。' } finally { loading.value = false }
}
const baseGrid = { left: 105, right: 22, top: 18, bottom: 24 }
const horizontalBar = (items: typeof clubs, score = false) => computed(() => ({ tooltip: { trigger: 'axis' }, grid: baseGrid, xAxis: { type: 'value', splitLine: { lineStyle: { color: '#edf2f1' } } }, yAxis: { type: 'category', inverse: true, data: items.value.map((item) => item.name ?? item.title), axisTick: { show: false }, axisLine: { show: false } }, series: [{ type: 'bar', barWidth: 12, data: items.value.map((item) => score ? item.activity_score : item.participations), itemStyle: { color: '#398b82', borderRadius: [0, 5, 5, 0] } }] }))
const trendOption = computed(() => ({ tooltip: { trigger: 'axis' }, legend: { data: ['参与人次', '活动数'] }, grid: { left: 48, right: 42, top: 42, bottom: 25 }, xAxis: { type: 'category', data: trends.value.map((item) => item.month) }, yAxis: [{ type: 'value' }, { type: 'value' }], series: [{ name: '参与人次', type: 'line', smooth: true, data: trends.value.map((item) => item.participations), areaStyle: { color: 'rgba(30,117,109,.1)' } }, { name: '活动数', type: 'bar', yAxisIndex: 1, data: trends.value.map((item) => item.activities), itemStyle: { color: '#d1954f' } }] }))
const clubOption = horizontalBar(clubs, true); const activityOption = horizontalBar(activities)
const studentOption = horizontalBar(students); const collegeOption = horizontalBar(colleges)
const pieOption = (items: typeof categories) => computed(() => ({ tooltip: { trigger: 'item' }, legend: { bottom: 0 }, series: [{ type: 'pie', radius: ['42%', '68%'], center: ['50%', '43%'], itemStyle: { borderColor: '#fff', borderWidth: 3 }, data: items.value.map((item) => ({ name: item.name, value: item.participations })) }] }))
const categoryOption = pieOption(categories); const campusOption = pieOption(campuses)
onMounted(loadAnalytics)
</script>

<template>
  <div class="workspace"><aside class="sidebar"><div class="brand"><span>S</span><div><strong>SZUT</strong><small>校园活动数据中心</small></div></div><nav><RouterLink to="/"><i>▦</i>数据总览</RouterLink><RouterLink to="/students"><i>◎</i>学生管理</RouterLink><RouterLink to="/clubs"><i>◇</i>社团管理</RouterLink><RouterLink to="/activities"><i>□</i>活动管理</RouterLink><RouterLink to="/participation"><i>✓</i>报名签到</RouterLink><RouterLink class="active" to="/analytics"><i>⌁</i>统计分析</RouterLink><RouterLink to="/agent"><i>✦</i>智能分析</RouterLink></nav><footer><b></b><div><strong>统一统计口径</strong><small>Statistics Service</small></div></footer></aside><main class="main"><header class="topbar"><div><p>多维数据洞察 / ANALYTICS</p><h1>统计分析</h1></div><span>{{ loading ? '数据计算中…' : '固定种子数据集' }}</span></header><section class="hero"><div><small>ANALYTICAL WORKBENCH</small><h2>从趋势、排名与结构，理解校园活力</h2><p>所有图表共享后端统计口径，可按学期、校区和时间范围联动筛选。</p></div></section><section class="filters"><label>学期<select v-model="filters.term_id"><option value="">全部学期</option><option v-for="item in contexts.terms" :key="item.id" :value="String(item.id)">{{ item.name }}</option></select></label><label>校区<select v-model="filters.campus_id"><option value="">全部校区</option><option v-for="item in contexts.campuses" :key="item.id" :value="String(item.id)">{{ item.name }}</option></select></label><label>开始日期<input v-model="filters.date_from" type="date" /></label><label>结束日期<input v-model="filters.date_to" type="date" /></label><button @click="loadAnalytics">应用筛选</button></section><p v-if="error" class="error">{{ error }}</p><section class="charts"><article class="wide"><header><small>01 / TREND</small><h3>月度活动与参与趋势</h3></header><VChart :option="trendOption" autoresize /></article><article><header><small>02 / CLUB</small><h3>社团综合活跃度</h3></header><VChart :option="clubOption" autoresize /></article><article><header><small>03 / ACTIVITY</small><h3>热门活动参与排行</h3></header><VChart :option="activityOption" autoresize /></article><article><header><small>04 / STUDENT</small><h3>学生参与排行</h3></header><VChart :option="studentOption" autoresize /></article><article><header><small>05 / COLLEGE</small><h3>学院参与排行</h3></header><VChart :option="collegeOption" autoresize /></article><article><header><small>06 / CATEGORY</small><h3>活动类别分布</h3></header><VChart :option="categoryOption" autoresize /></article><article><header><small>07 / CAMPUS</small><h3>校区活动参与分布</h3></header><VChart :option="campusOption" autoresize /></article></section></main></div>
</template>

<style scoped>
.workspace{min-height:100vh;color:#173737;background:#eef3f2}.sidebar{position:fixed;inset:0 auto 0 0;width:232px;display:flex;flex-direction:column;padding:28px 20px;color:#eaf6f3;background:#103f40}.brand{display:flex;align-items:center;gap:12px;padding:0 8px 28px;border-bottom:1px solid rgba(255,255,255,.12)}.brand>span{display:grid;place-items:center;width:38px;height:38px;border:1px solid #8ab3af;border-radius:50%;font:22px Georgia}.brand strong,.brand small{display:block}.brand strong{letter-spacing:.14em}.brand small{color:#a7cfca;font-size:10px}.sidebar nav{display:grid;gap:7px;margin-top:30px}.sidebar a{display:flex;align-items:center;gap:13px;border-radius:7px;padding:12px 14px;color:#b7d3d0;text-decoration:none;font-size:14px}.sidebar i{width:18px;font-style:normal}.sidebar a.active,.sidebar a:hover{color:#fff;background:rgba(255,255,255,.1)}.sidebar a.active{box-shadow:inset 3px 0 #e1a354}.sidebar footer{display:flex;align-items:center;gap:10px;margin-top:auto;border-top:1px solid rgba(255,255,255,.12);padding:16px 8px 0}.sidebar footer>b{width:8px;height:8px;border-radius:50%;background:#75c9a6}.sidebar footer strong,.sidebar footer small{display:block;font-size:10px}.sidebar footer small{color:#8dbcb7}.main{margin-left:232px;padding:0 34px 48px}.topbar{display:flex;align-items:center;justify-content:space-between;min-height:96px}.topbar p{margin:0 0 6px;color:#7b8e8d;font-size:11px}.topbar h1{margin:0;font:600 28px STZhongsong,"Songti SC",serif}.topbar>span{color:#7b8e8d;font-size:10px}.hero{border-radius:9px;padding:28px 34px;color:#fff;background:linear-gradient(110deg,#0c5753,#287b73)}.hero small,.charts small{color:#e2aa60;font-size:9px;letter-spacing:.14em}.hero h2{margin:8px 0 6px;font:500 25px STZhongsong}.hero p{margin:0;color:#cde2df;font-size:12px}.filters{display:grid;grid-template-columns:repeat(4,1fr) auto;gap:10px;margin:16px 0;border:1px solid #d8e1df;border-radius:8px;padding:16px 18px;background:#fff}.filters label{display:grid;gap:5px;color:#708482;font-size:9px}.filters select,.filters input{height:37px;border:1px solid #ccd8d6;border-radius:5px;padding:0 9px;color:#355251;background:#fafcfc}.filters button{align-self:end;height:37px;border:0;border-radius:5px;padding:0 18px;color:#fff;background:#17615d}.charts{display:grid;grid-template-columns:1fr 1fr;gap:15px}.charts article{min-width:0;border:1px solid #d7e0de;border-radius:8px;padding:19px;background:#fff}.charts article.wide{grid-column:1/-1}.charts header{height:43px}.charts h3{margin:5px 0 0;font-size:15px}.charts article>div{height:310px}.charts .wide>div{height:330px}.error{border-left:3px solid #bd7f34;padding:11px;color:#8c5720;background:#fff6ea;font-size:11px}
</style>
