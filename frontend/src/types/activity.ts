export interface ActivityListItem {
  id: number
  code: string
  title: string
  start_time: string
  end_time: string
  capacity: number
  status: 'draft' | 'published' | 'completed' | 'cancelled'
  club_id: number
  club_name: string
  category_id: number
  category_name: string
  term_id: number
  term_name: string
  venue_id: number
  venue_name: string
  campus_id: number
  campus_name: string
  registrations: number
  attendance: number
  attendance_rate: string | null
}

export interface ActivityListResponse {
  items: ActivityListItem[]
  total: number
  page: number
  page_size: number
  summary: {
    total_activities: number
    completed_activities: number
    registrations: number
    attendance: number
  }
  options: {
    terms: Array<{ id: number; name: string }>
    categories: Array<{ id: number; name: string }>
    clubs: Array<{ id: number; name: string }>
    campuses: Array<{ id: number; name: string }>
    venues: Array<{ id: number; name: string; campus_id: number }>
  }
}

export interface ActivityDetail {
  id: number
  code: string
  title: string
  description: string
  start_time: string
  end_time: string
  capacity: number
  status: ActivityListItem['status']
  created_at: string
  club_name: string
  category_name: string
  term_name: string
  venue_name: string
  venue_type: string
  campus_name: string
  metrics: {
    registrations: number
    attendance: number
    absent: number
    attendance_rate: string | null
  }
  registration_distribution: Array<{ status: string; count: number }>
  attendance_distribution: Array<{ status: string; count: number }>
  participants: Array<{
    id: number
    name: string
    student_no: string
    college_name: string
    registration_status: string
    attendance_status: string | null
    checkin_time: string | null
  }>
}
