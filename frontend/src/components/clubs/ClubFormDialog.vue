<script setup lang="ts">
import axios from 'axios'
import { reactive, watch } from 'vue'

import { http } from '@/api/http'
import type { ClubListItem, ClubListResponse } from '@/types/club'

const props = defineProps<{ open: boolean; club: ClubListItem | null; options?: ClubListResponse['options'] }>()
const emit = defineEmits<{ close: []; saved: [] }>()
const form = reactive({ code: '', name: '', category_id: 0, home_campus_id: 0, advisor_name: '', founded_date: '', description: '', status: 'active' as 'active' | 'inactive' })
const state = reactive({ saving: false, error: '' })

watch(() => [props.open, props.club] as const, () => {
  if (!props.open) return
  Object.assign(form, props.club ? {
    code: props.club.code, name: props.club.name, category_id: props.club.category_id,
    home_campus_id: props.club.campus_id, advisor_name: props.club.advisor_name ?? '',
    founded_date: props.club.founded_date ?? '', description: '', status: props.club.status,
  } : {
    code: '', name: '', category_id: props.options?.categories[0]?.id ?? 0,
    home_campus_id: props.options?.campuses[0]?.id ?? 0, advisor_name: '',
    founded_date: '', description: '', status: 'active',
  })
  state.error = ''
}, { immediate: true })

async function submit(): Promise<void> {
  state.saving = true
  state.error = ''
  const payload = {
    name: form.name, category_id: form.category_id, home_campus_id: form.home_campus_id,
    advisor_name: form.advisor_name || null, founded_date: form.founded_date || null,
    description: form.description || undefined, status: form.status,
  }
  try {
    if (props.club) await http.put(`/clubs/${props.club.id}`, payload)
    else await http.post('/clubs', { code: form.code, ...payload })
    emit('saved')
  } catch (reason) {
    state.error = axios.isAxiosError(reason) ? String(reason.response?.data?.message ?? '保存失败。') : '保存失败。'
  } finally { state.saving = false }
}
</script>

<template>
  <div v-if="open" class="mask" @click.self="emit('close')"><form @submit.prevent="submit"><header><div><small>CLUB PROFILE</small><h2>{{ club ? '编辑社团档案' : '新增校园社团' }}</h2></div><button type="button" @click="emit('close')">×</button></header><div class="grid"><label v-if="!club"><span>社团编号</span><input v-model.trim="form.code" required /></label><label><span>社团名称</span><input v-model.trim="form.name" required /></label><label><span>社团类别</span><select v-model.number="form.category_id"><option v-for="item in options?.categories" :key="item.id" :value="item.id">{{ item.name }}</option></select></label><label><span>所属校区</span><select v-model.number="form.home_campus_id"><option v-for="item in options?.campuses" :key="item.id" :value="item.id">{{ item.name }}</option></select></label><label><span>指导教师</span><input v-model.trim="form.advisor_name" /></label><label><span>成立日期</span><input v-model="form.founded_date" type="date" /></label><label><span>运行状态</span><select v-model="form.status"><option value="active">正常运行</option><option value="inactive">已停用</option></select></label><label class="wide"><span>社团简介</span><textarea v-model.trim="form.description" rows="4" placeholder="可在此补充或更新社团介绍" /></label></div><p v-if="state.error" class="error">{{ state.error }}</p><footer><button type="button" @click="emit('close')">取消</button><button class="primary" type="submit" :disabled="state.saving">{{ state.saving ? '保存中…' : '保存社团' }}</button></footer></form></div>
</template>

<style scoped>
.mask{position:fixed;inset:0;z-index:60;display:grid;place-items:center;background:rgba(8,39,39,.48);backdrop-filter:blur(3px)}form{width:min(700px,calc(100% - 60px));border-radius:10px;padding:26px 28px;background:#f9fbfa}header{display:flex;justify-content:space-between;border-bottom:1px solid #d9e3e1;padding-bottom:16px}header small{color:#b4772e;font-size:9px;letter-spacing:.15em}h2{margin:5px 0 0;font:600 23px STZhongsong,"Songti SC",serif}header button{border:0;background:none;font-size:25px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px 18px;margin-top:20px}label{display:grid;gap:7px;color:#627a78;font-size:10px}.wide{grid-column:1/-1}input,select,textarea{width:100%;border:1px solid #ccd9d6;border-radius:5px;padding:0 11px;color:#274746;background:#fff}input,select{height:40px}textarea{padding:10px;resize:vertical}.error{color:#955522;font-size:11px}footer{display:flex;justify-content:flex-end;gap:9px;margin-top:20px;border-top:1px solid #d9e3e1;padding-top:16px}footer button{height:38px;border:1px solid #bdcbc8;border-radius:5px;padding:0 17px;background:#fff}.primary{border-color:#155f5b;color:#fff;background:#155f5b}
</style>
