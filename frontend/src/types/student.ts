export interface StudentListItem {
  id: number
  student_no: string
  name: string
  gender: string
  grade_no: number
  class_name: string
  status: 'active' | 'graduated' | 'suspended'
  college_id: number
  college_name: string
  major_id: number
  major_name: string
  club_count: number
  participation_count: number
  last_activity_at: string | null
}

export interface StudentSummary {
  total_students: number
  college_count: number
  participating_students: number
  club_members: number
}

export interface StudentListResponse {
  items: StudentListItem[]
  total: number
  page: number
  page_size: number
  summary: StudentSummary
  options: {
    colleges: Array<{ id: number; name: string }>
    majors: Array<{ id: number; college_id: number; name: string }>
  }
}

export interface StudentDetail extends Omit<StudentListItem, 'club_count' | 'participation_count' | 'last_activity_at'> {
  enrollment_year: number
  created_at: string
  participation_summary: {
    club_count: number
    registration_count: number
    participation_count: number
    attendance_rate: string | null
  }
  clubs: Array<{
    id: number
    name: string
    category_name: string
    role: 'leader' | 'core' | 'member'
    join_date: string
  }>
  recent_activities: Array<{
    id: number
    title: string
    club_name: string
    category_name: string
    start_time: string
    attendance_status: 'present' | 'late' | 'absent'
  }>
}
