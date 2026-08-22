<script setup lang="ts">
import axios from 'axios'
import { computed, reactive, watch } from 'vue'

import { http } from '@/api/http'
import type { ActivityListItem, ActivityListResponse } from '@/types/activity'

const props = defineProps<{ open: boolean; activity: ActivityListItem | null; options?: ActivityListResponse['options'] }>()
const emit = defineEmits<{ close: []; saved: [] }>()
const form = reactive({ code: '', club_id: 0, category_id: 0, term_id: 0, venue_id: 0, title: '', description: '', start_time: '', end_time: '', capacity: 100, status: 'draft' as ActivityListItem['status'] })
const state = reactive({ saving: false, error: '' })
const selectedVenue = computed(() => props.options?.venues.find((item) => item.id === form.venue_id))

watch(() => [props.open, props.activity] as const, () => {
  if (!props.open) return
  const item = props.activity
  Object.assign(form, item ? {
    code: item.code, club_id: item.club_id, category_id: item.category_id,
    term_id: item.term_id, venue_id: item.venue_id, title: item.title, description: '',
    start_time: item.start_time.slice(0, 16), end_time: item.end_time.slice(0, 16),
    capacity: item.capacity, status: item.status,
  } : {
    code: '', club_id: props.options?.clubs[0]?.id ?? 0,
    category_id: props.options?.categories[0]?.id ?? 0, term_id: props.options?.terms[0]?.id ?? 0,
    venue_id: props.options?.venues[0]?.id ?? 0, title: '', description: '',
    start_time: '', end_time: '', capacity: 100, status: 'draft',
  })
  state.error = ''
}, { immediate: true })

async function submit(): Promise<void> {
  state.saving = true
  state.error = ''
  const payload = {
    category_id: form.category_id, term_id: form.term_id, venue_id: form.venue_id,
    title: form.title, description: form.description || undefined,
    start_time: form.start_time, end_time: form.end_time,
    capacity: form.capacity, status: form.status,
  }
  try {
    if (props.activity) await http.put(`/activities/${props.activity.id}`, payload)
    else await http.post('/activities', { code: form.code, club_id: form.club_id, ...payload })
    emit('saved')
  } catch (reason) {
    state.error = axios.isAxiosError(reason) ? String(reason.response?.data?.message ?? '保存失败。') : '保存失败。'
  } finally { state.saving = false }
}
</script>

<template>
  <div v-if="open" class="mask" @click.self="emit('close')"><form @submit.prevent="submit"><header><div><small>ACTIVITY OPERATION</small><h2>{{ activity ? '编辑活动信息' : '新建校园活动' }}</h2></div><button type="button" @click="emit('close')">×</button></header><div class="grid"><label v-if="!activity"><span>活动编号</span><input v-model.trim="form.code" required /></label><label><span>活动名称</span><input v-model.trim="form.title" required /></label><label v-if="!activity"><span>举办社团</span><select v-model.number="form.club_id"><option v-for="item in options?.clubs" :key="item.id" :value="item.id">{{ item.name }}</option></select></label><label><span>活动类别</span><select v-model.number="form.category_id"><option v-for="item in options?.categories" :key="item.id" :value="item.id">{{ item.name }}</option></select></label><label><span>所属学期</span><select v-model.number="form.term_id"><option v-for="item in options?.terms" :key="item.id" :value="item.id">{{ item.name }}</option></select></label><label><span>举办场地</span><select v-model.number="form.venue_id"><option v-for="item in options?.venues" :key="item.id" :value="item.id">{{ item.name }}</option></select><small>{{ selectedVenue ? `校区编号 ${selectedVenue.campus_id}` : '' }}</small></label><label><span>开始时间</span><input v-model="form.start_time" type="datetime-local" required /></label><label><span>结束时间</span><input v-model="form.end_time" type="datetime-local" required /></label><label><span>活动容量</span><input v-model.number="form.capacity" type="number" min="1" required /></label><label><span>活动状态</span><select v-model="form.status"><option value="draft">草稿</option><option value="published">已发布</option><option value="completed">已完成</option><option value="cancelled">已取消</option></select></label><label class="wide"><span>活动说明</span><textarea v-model.trim="form.description" rows="3" /></label></div><p v-if="state.error" class="error">{{ state.error }}</p><footer><button type="button" @click="emit('close')">取消</button><button class="primary" type="submit" :disabled="state.saving">{{ state.saving ? '保存中…' : '保存活动' }}</button></footer></form></div>
</template>

<style scoped>
.mask{position:fixed;inset:0;z-index:60;display:grid;place-items:center;background:rgba(8,39,39,.48);backdrop-filter:blur(3px)}form{width:min(760px,calc(100% - 60px));border-radius:10px;padding:25px 28px;background:#f9fbfa}header{display:flex;justify-content:space-between;border-bottom:1px solid #d9e3e1;padding-bottom:15px}header small{color:#b4772e;font-size:9px;letter-spacing:.15em}h2{margin:5px 0 0;font:600 23px STZhongsong,"Songti SC",serif}header button{border:0;background:none;font-size:25px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:13px 18px;margin-top:19px}label{display:grid;gap:6px;color:#627a78;font-size:10px}.wide{grid-column:1/-1}input,select,textarea{width:100%;border:1px solid #ccd9d6;border-radius:5px;padding:0 10px;color:#274746;background:#fff}input,select{height:39px}textarea{padding:9px;resize:vertical}label small{color:#95a5a3}.error{color:#955522;font-size:11px}footer{display:flex;justify-content:flex-end;gap:9px;margin-top:19px;border-top:1px solid #d9e3e1;padding-top:15px}footer button{height:38px;border:1px solid #bdcbc8;border-radius:5px;padding:0 17px;background:#fff}.primary{border-color:#155f5b;color:#fff;background:#155f5b}
</style>
