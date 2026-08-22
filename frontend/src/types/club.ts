export interface ClubListItem {
  id: number
  code: string
  name: string
  advisor_name: string
  founded_date: string
  status: 'active' | 'inactive'
  category_id: number
  category_name: string
  campus_id: number
  campus_name: string
  leader_name: string
  member_count: number
  activity_count: number
  participation_count: number
}

export interface ClubListResponse {
  items: ClubListItem[]
  total: number
  page: number
  page_size: number
  summary: {
    active_clubs: number
    category_count: number
    memberships: number
    completed_activities: number
  }
  options: {
    categories: Array<{ id: number; name: string }>
    campuses: Array<{ id: number; name: string }>
  }
}

export interface ClubDetail {
  id: number
  code: string
  name: string
  advisor_name: string
  founded_date: string
  description: string
  status: 'active' | 'inactive'
  category_name: string
  campus_name: string
  leader_name: string
  leader_student_no: string
  metrics: {
    member_count: number
    core_member_count: number
    activity_count: number
    registration_count: number
    participation_count: number
    attendance_rate: string | null
  }
  role_distribution: Array<{ role: 'leader' | 'core' | 'member'; count: number }>
  recent_activities: Array<{
    id: number
    title: string
    category_name: string
    start_time: string
    status: string
    capacity: number
    venue_name: string
    registrations: number
    attendance: number
  }>
  active_members: Array<{
    id: number
    name: string
    student_no: string
    college_name: string
    role: 'leader' | 'core' | 'member'
    participations: number
  }>
}
