<script setup lang="ts">
import axios from 'axios'
import { computed, reactive, watch } from 'vue'

import { http } from '@/api/http'
import type { StudentDetail, StudentListResponse } from '@/types/student'

interface StudentForm {
  student_no?: string
  name: string
  gender: string
  college_id: number
  major_id: number
  enrollment_year: number
  grade_no: number
  class_name: string
  status: 'active' | 'graduated' | 'suspended'
}

const props = defineProps<{
  open: boolean
  student: StudentDetail | null
  options: StudentListResponse['options'] | undefined
}>()
const emit = defineEmits<{ close: []; saved: [] }>()
const form = reactive<StudentForm>({
  student_no: '', name: '', gender: '男', college_id: 0, major_id: 0,
  enrollment_year: new Date().getFullYear(), grade_no: 1, class_name: '', status: 'active',
})
const state = reactive({ saving: false, error: '' })
const majors = computed(() => props.options?.majors.filter((item) => item.college_id === form.college_id) ?? [])

watch(() => [props.open, props.student] as const, () => {
  if (!props.open) return
  const student = props.student
  Object.assign(form, student ? {
    name: student.name, gender: student.gender, college_id: student.college_id,
    major_id: student.major_id, enrollment_year: student.enrollment_year,
    grade_no: student.grade_no, class_name: student.class_name, status: student.status,
  } : {
    student_no: '', name: '', gender: '男', college_id: props.options?.colleges[0]?.id ?? 0,
    major_id: props.options?.majors[0]?.id ?? 0, enrollment_year: new Date().getFullYear(),
    grade_no: 1, class_name: '', status: 'active',
  })
  state.error = ''
}, { immediate: true })

async function submit(): Promise<void> {
  state.saving = true
  state.error = ''
  try {
    if (props.student) {
      const { student_no: _studentNo, ...payload } = form
      await http.put(`/students/${props.student.id}`, payload)
    } else {
      await http.post('/students', form)
    }
    emit('saved')
  } catch (reason) {
    state.error = axios.isAxiosError(reason)
      ? String(reason.response?.data?.message ?? '保存失败，请检查填写内容。')
      : '保存失败，请稍后重试。'
  } finally {
    state.saving = false
  }
}
</script>

<template>
  <div v-if="open" class="modal-mask" @click.self="emit('close')">
    <form class="form-card" @submit.prevent="submit">
      <header><div><small>STUDENT PROFILE</small><h2>{{ student ? '编辑学生档案' : '新增学生档案' }}</h2></div><button type="button" @click="emit('close')">×</button></header>
      <div class="form-grid">
        <label v-if="!student"><span>学号</span><input v-model.trim="form.student_no" required maxlength="30" /></label>
        <label><span>姓名</span><input v-model.trim="form.name" required maxlength="50" /></label>
        <label><span>性别</span><select v-model="form.gender"><option>男</option><option>女</option></select></label>
        <label><span>入学年份</span><input v-model.number="form.enrollment_year" type="number" min="2000" max="2100" required /></label>
        <label><span>学院</span><select v-model.number="form.college_id" required><option v-for="item in options?.colleges" :key="item.id" :value="item.id">{{ item.name }}</option></select></label>
        <label><span>专业</span><select v-model.number="form.major_id" required><option v-for="item in majors" :key="item.id" :value="item.id">{{ item.name }}</option></select></label>
        <label><span>年级</span><select v-model.number="form.grade_no"><option v-for="grade in 4" :key="grade" :value="grade">{{ grade }} 年级</option></select></label>
        <label><span>班级</span><input v-model.trim="form.class_name" required maxlength="50" /></label>
        <label><span>状态</span><select v-model="form.status"><option value="active">在校</option><option value="graduated">已毕业</option><option value="suspended">暂停</option></select></label>
      </div>
      <p v-if="state.error" class="form-error">{{ state.error }}</p>
      <footer><button type="button" @click="emit('close')">取消</button><button class="primary" type="submit" :disabled="state.saving">{{ state.saving ? '正在保存…' : '保存档案' }}</button></footer>
    </form>
  </div>
</template>

<style scoped>
.modal-mask{position:fixed;inset:0;z-index:60;display:grid;place-items:center;padding:30px;background:rgba(8,39,39,.48);backdrop-filter:blur(3px)}.form-card{width:min(720px,100%);border-radius:10px;padding:26px 28px;background:#f9fbfa;box-shadow:0 24px 70px rgba(5,34,33,.22)}header{display:flex;justify-content:space-between;border-bottom:1px solid #d9e3e1;padding-bottom:17px}header small{color:#b4772e;font-size:9px;font-weight:700;letter-spacing:.15em}h2{margin:5px 0 0;font:600 23px STZhongsong,"Songti SC",serif}header button{border:0;color:#718482;background:none;font-size:26px;cursor:pointer}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:15px 18px;margin-top:22px}label{display:grid;gap:7px;color:#627a78;font-size:10px}input,select{height:41px;border:1px solid #ccd9d6;border-radius:5px;padding:0 11px;color:#274746;background:#fff;outline:none}input:focus,select:focus{border-color:#3b8b83}.form-error{margin:16px 0 0;color:#955522;font-size:11px}footer{display:flex;justify-content:flex-end;gap:9px;margin-top:24px;border-top:1px solid #d9e3e1;padding-top:17px}footer button{height:38px;border:1px solid #bfcfcb;border-radius:5px;padding:0 18px;color:#4f6c69;background:#fff;cursor:pointer}.primary{border-color:#135d59;color:#fff;background:#135d59}
</style>
