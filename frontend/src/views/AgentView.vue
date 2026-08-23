<script setup lang="ts">
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { computed, nextTick, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import VChart from 'vue-echarts'

import {
  deleteAgentConversation,
  listAgentConversations,
  listAgentMessages,
  sendAgentMessage,
} from '@/api/agent'
import { http } from '@/api/http'
import campusPhoto from '@/assets/campus/zichuan-bridge.jpg'
import type {
  AgentChatResponse,
  AgentConversation,
  AgentMessage,
  DictionaryItem,
} from '@/types/agent'

use([CanvasRenderer, BarChart, LineChart, PieChart, GridComponent, LegendComponent, TooltipComponent])

type DisplayMessage = AgentMessage & { response?: AgentChatResponse }

const conversations = ref<AgentConversation[]>([])
const messages = ref<DisplayMessage[]>([])
const activeConversationId = ref<number | null>(null)
const question = ref('')
const sending = ref(false)
const error = ref('')
const messagePanel = ref<HTMLElement | null>(null)
const latestResponse = ref<AgentChatResponse | null>(null)
const terms = ref<DictionaryItem[]>([])
const campuses = ref<DictionaryItem[]>([])
const termId = ref('')
const campusId = ref('')

const quickQuestions = [
  '本学期社团活动参与情况怎么样？',
  '列出最活跃的 5 个社团',
  '展示各月参与人次趋势',
  '不同活动类别的参与分布如何？',
]

const toolNames: Record<string, string> = {
  get_overview_statistics: '总体概览',
  get_club_ranking: '社团排行',
  get_activity_ranking: '活动排行',
  get_participation_trend: '参与趋势',
  get_distribution_statistics: '结构分布',
  get_student_summary: '学生参与画像',
  get_club_summary: '社团数据摘要',
}

const chartOption = computed(() => {
  const visualization = latestResponse.value?.visualization
  if (!visualization) return {}
  const isPie = visualization.type === 'pie'
  return {
    color: ['#0b625f', '#d09245', '#57a397', '#557d91', '#8abbb3'],
    tooltip: { trigger: isPie ? 'item' : 'axis' },
    legend: isPie ? { bottom: 0, textStyle: { color: '#607572', fontSize: 10 } } : undefined,
    grid: isPie ? undefined : { left: 52, right: 18, top: 22, bottom: 58 },
    xAxis: isPie
      ? undefined
      : {
          type: 'category',
          data: visualization.categories,
          axisLabel: { rotate: visualization.categories.length > 5 ? 28 : 0, color: '#718582' },
          axisLine: { lineStyle: { color: '#ccd9d6' } },
        },
    yAxis: isPie
      ? undefined
      : { type: 'value', splitLine: { lineStyle: { color: '#edf2f1' } } },
    series: visualization.series.map((series) => ({
      name: series.name,
      type: visualization.type,
      data: series.data,
      smooth: visualization.type === 'line',
      barMaxWidth: 26,
      radius: visualization.type === 'pie' ? ['42%', '68%'] : undefined,
      itemStyle: visualization.type === 'bar' ? { borderRadius: [5, 5, 0, 0] } : undefined,
      areaStyle: visualization.type === 'line' ? { color: 'rgba(11,98,95,.08)' } : undefined,
    })),
  }
})

const dataRows = computed(() => {
  const data = latestResponse.value?.data
  if (Array.isArray(data)) return data.filter((item): item is Record<string, unknown> => Boolean(item && typeof item === 'object')).slice(0, 8)
  if (data && typeof data === 'object') return [data as Record<string, unknown>]
  return []
})

const dataColumns = computed(() => Object.keys(dataRows.value[0] ?? {}).filter((key) => !['id', 'start_time'].includes(key)).slice(0, 4))
const currentTitle = computed(() => conversations.value.find((item) => item.id === activeConversationId.value)?.title ?? '新分析')

function displayValue(value: unknown): string {
  if (value === null || value === undefined) return '—'
  return typeof value === 'number' ? new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 2 }).format(value) : String(value)
}

function formatTime(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(value))
}

async function loadConversations(): Promise<void> {
  conversations.value = await listAgentConversations()
}

async function openConversation(id: number): Promise<void> {
  activeConversationId.value = id
  latestResponse.value = null
  messages.value = await listAgentMessages(id)
  await scrollToBottom()
}

function newConversation(): void {
  activeConversationId.value = null
  messages.value = []
  latestResponse.value = null
  error.value = ''
  question.value = ''
}

async function removeConversation(id: number): Promise<void> {
  if (!window.confirm('确定删除这条分析会话吗？')) return
  await deleteAgentConversation(id)
  if (activeConversationId.value === id) newConversation()
  await loadConversations()
}

async function scrollToBottom(): Promise<void> {
  await nextTick()
  if (messagePanel.value) messagePanel.value.scrollTop = messagePanel.value.scrollHeight
}

async function submit(): Promise<void> {
  const content = question.value.trim()
  if (!content || sending.value) return
  error.value = ''
  question.value = ''
  const optimistic: DisplayMessage = {
    id: -Date.now(),
    role: 'user',
    content,
    model_used: null,
    tool_calls: [],
    created_at: new Date().toISOString(),
  }
  messages.value.push(optimistic)
  sending.value = true
  await scrollToBottom()
  try {
    const response = await sendAgentMessage(content, activeConversationId.value, {
      term_id: termId.value ? Number(termId.value) : undefined,
      campus_id: campusId.value ? Number(campusId.value) : undefined,
    })
    activeConversationId.value = response.conversation_id
    latestResponse.value = response
    messages.value.push({
      id: Date.now(),
      role: 'assistant',
      content: response.answer,
      model_used: response.model_used,
      tool_calls: response.tool_calls,
      created_at: new Date().toISOString(),
      response,
    })
    await loadConversations()
  } catch {
    messages.value = messages.value.filter((item) => item !== optimistic)
    question.value = content
    error.value = '本地智能分析暂时未完成，请确认 Hermes、Ollama 与 FastAPI 均在运行后重试。'
  } finally {
    sending.value = false
    await scrollToBottom()
  }
}

function askQuick(text: string): void {
  question.value = text
  void submit()
}

onMounted(async () => {
  try {
    const [conversationItems, termResponse, campusResponse] = await Promise.all([
      listAgentConversations(),
      http.get<{ items: DictionaryItem[] }>('/dictionaries/terms'),
      http.get<{ items: DictionaryItem[] }>('/dictionaries/campuses'),
    ])
    conversations.value = conversationItems
    terms.value = termResponse.data.items
    campuses.value = campusResponse.data.items
  } catch {
    error.value = 'Agent 工作台初始化失败，请检查后端服务。'
  }
})
</script>

<template>
  <div class="workspace">
    <aside class="sidebar">
      <div class="brand"><span>S</span><div><strong>SZUT</strong><small>校园活动数据中心</small></div></div>
      <nav>
        <RouterLink to="/"><i>▦</i>数据总览</RouterLink>
        <RouterLink to="/students"><i>◎</i>学生管理</RouterLink>
        <RouterLink to="/clubs"><i>◇</i>社团管理</RouterLink>
        <RouterLink to="/activities"><i>□</i>活动管理</RouterLink>
        <RouterLink to="/participation"><i>✓</i>报名签到</RouterLink>
        <RouterLink to="/analytics"><i>⌁</i>统计分析</RouterLink>
        <RouterLink class="active" to="/agent"><i>✦</i>智能分析</RouterLink>
      </nav>
      <div class="campus-card" :style="{ backgroundImage: `linear-gradient(rgba(10,63,62,.22),rgba(10,63,62,.82)),url(${campusPhoto})` }"><span>苏州工学院</span><strong>让数据回应校园</strong></div>
      <footer><b></b><div><strong>本地模型已接入</strong><small>Hermes × Ollama</small></div></footer>
    </aside>

    <main class="main">
      <header class="topbar">
        <div><p>AI DATA INQUIRY / CAMPUS AGENT</p><h1>校园数据研判台</h1></div>
        <div class="filters"><label>学期<select v-model="termId"><option value="">全部学期</option><option v-for="item in terms" :key="item.id" :value="String(item.id)">{{ item.name }}</option></select></label><label>校区<select v-model="campusId"><option value="">全部校区</option><option v-for="item in campuses" :key="item.id" :value="String(item.id)">{{ item.name }}</option></select></label></div>
      </header>

      <section class="studio">
        <aside class="history-panel">
          <button class="new-button" type="button" @click="newConversation"><span>＋</span>发起新分析</button>
          <div class="panel-label"><span>分析档案</span><small>{{ conversations.length }} 条会话</small></div>
          <div class="conversation-list">
            <article v-for="item in conversations" :key="item.id" :class="{ active: item.id === activeConversationId }" @click="openConversation(item.id)">
              <div><strong>{{ item.title }}</strong><small>{{ formatTime(item.updated_at) }} · {{ item.message_count }} 条消息</small></div>
              <button aria-label="删除会话" type="button" @click.stop="removeConversation(item.id)">×</button>
            </article>
            <p v-if="!conversations.length" class="empty-list">尚无分析记录<br />从一个问题开始</p>
          </div>
          <div class="scope-note"><span>当前数据范围</span><strong>{{ termId ? '指定学期' : '全部学期' }} · {{ campusId ? '指定校区' : '全部校区' }}</strong><small>权限随当前登录账号自动生效</small></div>
        </aside>

        <section class="dialog-panel">
          <header class="dialog-head"><div><span class="agent-mark">AI</span><div><strong>{{ currentTitle }}</strong><small><b></b>本地数据 Agent 在线</small></div></div><em>数据经工具核验</em></header>
          <div ref="messagePanel" class="messages">
            <div v-if="!messages.length" class="welcome">
              <span class="orbit">✦</span><p>校园社团活动智能分析</p><h2>想从数据中了解什么？</h2><p class="intro">我会调用本地统计工具查询 MySQL，并把依据、数据和图表一起呈现给你。</p>
              <div class="quick-grid"><button v-for="item in quickQuestions" :key="item" type="button" @click="askQuick(item)"><span>↗</span>{{ item }}</button></div>
            </div>
            <article v-for="message in messages" :key="message.id" class="message" :class="`message--${message.role}`">
              <span class="speaker">{{ message.role === 'user' ? '我' : 'AI' }}</span>
              <div><p>{{ message.content }}</p><footer><time>{{ formatTime(message.created_at) }}</time><span v-if="message.tool_calls.length">✓ {{ message.tool_calls.length }} 项数据核验</span><span v-if="message.model_used">{{ message.model_used }}</span></footer></div>
            </article>
            <article v-if="sending" class="message message--assistant"><span class="speaker">AI</span><div class="thinking"><i></i><i></i><i></i><p>正在调用校园统计工具进行研判…</p></div></article>
          </div>
          <p v-if="error" class="error">{{ error }}</p>
          <form class="composer" @submit.prevent="submit"><textarea v-model="question" rows="2" maxlength="2000" placeholder="输入你的统计问题，例如：本学期哪些社团参与度最高？" @keydown.ctrl.enter="submit"></textarea><div><span>Ctrl + Enter 发送 · 所有数值优先调用工具核验</span><button :disabled="sending || !question.trim()" type="submit">{{ sending ? '研判中' : '发送分析' }} <b>↑</b></button></div></form>
        </section>

        <aside class="evidence-panel">
          <header><span>DATA EVIDENCE</span><h2>数据证据</h2><p>展示本次回答实际调用的统计工具与结构化结果。</p></header>
          <template v-if="latestResponse">
            <section class="tool-trace"><div class="section-title"><span>工具调用链</span><small>{{ latestResponse.tool_calls.length }} TOOLS</small></div><article v-for="(tool, index) in latestResponse.tool_calls" :key="`${tool.name}-${index}`"><i>{{ index + 1 }}</i><div><strong>{{ toolNames[tool.name] ?? tool.name }}</strong><small>{{ tool.success ? '数据返回成功' : tool.error }}</small></div><b :class="{ failed: !tool.success }">{{ tool.success ? '✓' : '!' }}</b></article></section>
            <section v-if="latestResponse.visualization" class="chart-card"><div class="section-title"><span>{{ latestResponse.visualization.title }}</span><small>ECHARTS</small></div><VChart :option="chartOption" autoresize /></section>
            <section v-if="dataRows.length" class="data-card"><div class="section-title"><span>关键数据</span><small>LIVE MYSQL</small></div><div class="mini-table"><div v-for="(row, index) in dataRows" :key="index" class="data-row"><span v-for="column in dataColumns" :key="column"><small>{{ column }}</small><strong>{{ displayValue(row[column]) }}</strong></span></div></div></section>
            <div class="model-note"><span>推理模型</span><strong>{{ latestResponse.model_used }}</strong><small>回答与数据证据分离存储</small></div>
          </template>
          <div v-else class="evidence-empty"><span>⌁</span><strong>等待一次数据研判</strong><p>提问后，这里会显示工具调用、图表与关键数据。</p></div>
        </aside>
      </section>
    </main>
  </div>
</template>

<style scoped>
.workspace{min-height:100vh;color:#173737;background:#eaf0ef}.sidebar{position:fixed;inset:0 auto 0 0;width:222px;display:flex;flex-direction:column;padding:27px 18px 20px;color:#eaf6f3;background:#103f40}.brand{display:flex;align-items:center;gap:11px;padding:0 8px 25px;border-bottom:1px solid rgba(255,255,255,.12)}.brand>span{display:grid;place-items:center;width:37px;height:37px;border:1px solid #8ab3af;border-radius:50%;font:21px Georgia}.brand strong,.brand small{display:block}.brand strong{letter-spacing:.14em}.brand small{color:#a7cfca;font-size:9px}.sidebar nav{display:grid;gap:5px;margin-top:25px}.sidebar a{display:flex;align-items:center;gap:12px;border-radius:7px;padding:11px 13px;color:#b7d3d0;text-decoration:none;font-size:13px}.sidebar i{width:18px;font-style:normal}.sidebar a.active,.sidebar a:hover{color:#fff;background:rgba(255,255,255,.1)}.sidebar a.active{box-shadow:inset 3px 0 #e1a354}.campus-card{display:flex;flex-direction:column;justify-content:flex-end;min-height:112px;margin-top:auto;border:1px solid rgba(255,255,255,.12);border-radius:8px;padding:15px;background-position:center;background-size:cover}.campus-card span{color:#c0dcd7;font-size:9px}.campus-card strong{margin-top:4px;font:500 14px STZhongsong,"Songti SC",serif}.sidebar footer{display:flex;align-items:center;gap:9px;margin-top:13px;padding:12px 6px 0}.sidebar footer>b{width:7px;height:7px;border-radius:50%;background:#75c9a6;box-shadow:0 0 0 4px rgba(117,201,166,.1)}.sidebar footer strong,.sidebar footer small{display:block;font-size:9px}.sidebar footer small{margin-top:2px;color:#8dbcb7}.main{min-width:1000px;margin-left:222px;padding:0 25px 28px}.topbar{display:flex;align-items:center;justify-content:space-between;min-height:84px}.topbar p{margin:0 0 5px;color:#718886;font-size:9px;letter-spacing:.15em}.topbar h1{margin:0;font:600 25px STZhongsong,"Songti SC",serif}.filters{display:flex;gap:9px}.filters label{display:grid;gap:4px;color:#708482;font-size:8px}.filters select{width:145px;height:34px;border:1px solid #cbd8d5;border-radius:5px;padding:0 9px;color:#355251;background:#fff}.studio{display:grid;grid-template-columns:220px minmax(460px,1fr) 310px;overflow:hidden;height:calc(100vh - 108px);min-height:650px;border:1px solid #cfdcda;border-radius:10px;background:#fff;box-shadow:0 15px 42px rgba(27,62,61,.08)}.history-panel{display:flex;min-width:0;flex-direction:column;border-right:1px solid #dbe4e2;padding:17px;background:#f6f9f8}.new-button{height:42px;border:0;border-radius:6px;color:#fff;background:#17615d;cursor:pointer}.new-button span{margin-right:7px;font-size:17px}.panel-label,.section-title{display:flex;align-items:center;justify-content:space-between}.panel-label{margin:22px 3px 9px;color:#647b78;font-size:10px}.panel-label small,.section-title small{color:#99aaa7;font-size:8px;letter-spacing:.08em}.conversation-list{overflow-y:auto}.conversation-list article{display:flex;align-items:center;gap:5px;margin-bottom:5px;border-radius:6px;padding:11px 8px 11px 10px;cursor:pointer}.conversation-list article:hover,.conversation-list article.active{background:#e6f0ee}.conversation-list article.active{box-shadow:inset 2px 0 #c98938}.conversation-list article>div{min-width:0;flex:1}.conversation-list strong,.conversation-list small{display:block}.conversation-list strong{overflow:hidden;color:#294643;font-size:11px;font-weight:600;text-overflow:ellipsis;white-space:nowrap}.conversation-list small{margin-top:5px;color:#8da09d;font-size:8px}.conversation-list button{border:0;color:#91a29f;background:transparent;cursor:pointer}.empty-list{padding:35px 10px;color:#9aaba8;text-align:center;font-size:10px;line-height:1.8}.scope-note{margin-top:auto;border-top:1px solid #dce5e3;padding:14px 4px 2px}.scope-note span,.scope-note strong,.scope-note small{display:block}.scope-note span{color:#94a4a2;font-size:8px}.scope-note strong{margin:5px 0;color:#385753;font-size:10px}.scope-note small{color:#9caaa8;font-size:8px}.dialog-panel{display:flex;min-width:0;flex-direction:column;background:#fbfdfc}.dialog-head{display:flex;align-items:center;justify-content:space-between;height:67px;border-bottom:1px solid #e0e7e5;padding:0 20px;background:#fff}.dialog-head>div{display:flex;align-items:center;gap:10px}.agent-mark{display:grid;place-items:center;width:33px;height:33px;border-radius:8px;color:#fff;background:#1c6a65;font:600 10px Bahnschrift}.dialog-head strong,.dialog-head small{display:block}.dialog-head strong{max-width:330px;overflow:hidden;font-size:12px;text-overflow:ellipsis;white-space:nowrap}.dialog-head small{margin-top:4px;color:#819592;font-size:8px}.dialog-head small b{display:inline-block;width:5px;height:5px;margin-right:5px;border-radius:50%;background:#52ae85}.dialog-head em{color:#97703e;font-size:8px;font-style:normal;letter-spacing:.08em}.messages{flex:1;overflow-y:auto;padding:24px 26px}.welcome{max-width:600px;margin:38px auto;text-align:center}.orbit{display:grid;place-items:center;width:55px;height:55px;margin:0 auto 18px;border:1px solid #70a39c;border-radius:50%;color:#c88839;background:#edf6f4;box-shadow:0 0 0 10px #f5f9f8}.welcome>p{margin:0;color:#b37a34;font-size:9px;letter-spacing:.13em}.welcome h2{margin:9px 0;font:500 24px STZhongsong,"Songti SC",serif}.welcome .intro{max-width:430px;margin:0 auto;color:#748985;font-size:10px;line-height:1.7;letter-spacing:0}.quick-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:25px}.quick-grid button{display:flex;align-items:center;gap:9px;min-height:48px;border:1px solid #d5e1df;border-radius:6px;padding:9px 12px;color:#49625f;background:#fff;text-align:left;font-size:10px;cursor:pointer}.quick-grid button:hover{border-color:#72aaa3;background:#f1f8f6}.quick-grid span{color:#bd7f35}.message{display:flex;max-width:84%;gap:10px;margin-bottom:19px}.message--user{margin-left:auto;flex-direction:row-reverse}.speaker{display:grid;place-items:center;flex:0 0 29px;width:29px;height:29px;border-radius:7px;color:#fff;background:#25726c;font-size:9px}.message--user .speaker{background:#c28740}.message>div{min-width:0}.message p{margin:0;border:1px solid #dce6e4;border-radius:3px 10px 10px;padding:11px 14px;color:#38514e;background:#fff;font-size:11px;line-height:1.8;white-space:pre-wrap}.message--user p{border:0;border-radius:10px 3px 10px 10px;color:#fff;background:#1d6863}.message footer{display:flex;gap:8px;margin-top:5px;color:#94a5a2;font-size:8px}.message footer span:first-of-type{color:#42877f}.thinking{display:flex;align-items:center;gap:4px;border:1px solid #dce6e4;border-radius:3px 10px 10px;padding:11px 14px;background:#fff}.thinking i{width:5px;height:5px;border-radius:50%;background:#4c938b;animation:pulse 1.1s infinite}.thinking i:nth-child(2){animation-delay:.15s}.thinking i:nth-child(3){animation-delay:.3s}.thinking p{border:0;padding:0 0 0 6px;color:#77908c;background:transparent}.error{margin:0 22px 8px;border-left:2px solid #c38338;padding:8px 11px;color:#885b27;background:#fff5e9;font-size:9px}.composer{margin:0 20px 18px;border:1px solid #cbdad7;border-radius:8px;padding:10px 12px;background:#fff;box-shadow:0 6px 20px rgba(36,75,72,.07)}.composer textarea{width:100%;resize:none;border:0;outline:0;color:#2c4946;font-size:11px;line-height:1.6}.composer>div{display:flex;align-items:center;justify-content:space-between;border-top:1px solid #edf1f0;padding-top:8px}.composer span{color:#99aaa7;font-size:8px}.composer button{height:31px;border:0;border-radius:5px;padding:0 11px;color:#fff;background:#17615d;font-size:9px;cursor:pointer}.composer button:disabled{opacity:.45;cursor:default}.composer b{margin-left:5px}.evidence-panel{overflow-y:auto;border-left:1px solid #dbe4e2;padding:18px;background:#f6f9f8}.evidence-panel>header{border-bottom:1px solid #dbe4e2;padding:2px 3px 15px}.evidence-panel>header span{color:#c0843d;font-size:8px;letter-spacing:.14em}.evidence-panel>header h2{margin:5px 0;font:600 17px STZhongsong,"Songti SC",serif}.evidence-panel>header p{margin:0;color:#849794;font-size:9px;line-height:1.6}.section-title{margin-bottom:10px;color:#526a67;font-size:9px}.tool-trace,.chart-card,.data-card{margin-top:16px;border:1px solid #d7e2df;border-radius:7px;padding:12px;background:#fff}.tool-trace article{display:flex;align-items:center;gap:8px;border-top:1px solid #eef2f1;padding:9px 0}.tool-trace article:first-of-type{border-top:0}.tool-trace article i{display:grid;place-items:center;width:19px;height:19px;border-radius:50%;color:#fff;background:#28736d;font-size:8px;font-style:normal}.tool-trace article div{min-width:0;flex:1}.tool-trace strong,.tool-trace small{display:block}.tool-trace strong{font-size:9px}.tool-trace small{margin-top:3px;color:#8fa09d;font-size:8px}.tool-trace article>b{color:#438c78}.tool-trace article>b.failed{color:#b56f35}.chart-card>div+div{height:210px}.mini-table{overflow-x:auto}.data-row{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px;border-top:1px solid #edf2f1;padding:8px 0}.data-row:first-child{border-top:0}.data-row span{min-width:0}.data-row small,.data-row strong{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.data-row small{color:#9aaba8;font-size:7px}.data-row strong{margin-top:2px;color:#395551;font-size:9px}.model-note{margin-top:15px;border-left:2px solid #c78a40;padding:7px 10px}.model-note span,.model-note strong,.model-note small{display:block}.model-note span{color:#8b9b99;font-size:7px}.model-note strong{margin:3px 0;font-size:9px}.model-note small{color:#9aa9a7;font-size:7px}.evidence-empty{margin:75px auto 0;color:#92a4a1;text-align:center}.evidence-empty>span{display:grid;place-items:center;width:43px;height:43px;margin:0 auto 13px;border:1px solid #b8cac7;border-radius:50%;font-size:17px}.evidence-empty strong{display:block;color:#657c79;font-size:10px}.evidence-empty p{font-size:8px;line-height:1.7}@keyframes pulse{50%{opacity:.25;transform:translateY(-2px)}}
</style>