export interface Overview {
  active_clubs: number
  completed_activities: number
  participations: number
  active_students: number
  attendance_rate: number | null
}

export interface TrendPoint {
  month: string
  activities: number
  participations: number
}

export interface RankingItem {
  id: number
  name: string
  activities?: number
  participations: number
  students?: number
}

export interface CategoryItem extends RankingItem {
  activities: number
}

export interface ActivityItem {
  id: number
  title: string
  club_name: string
  start_time: string
  registrations: number
  attendance: number
  attendance_rate: string
}

export interface ContextOption {
  id: number
  name: string
  is_default?: boolean
}

export interface DashboardResponse {
  overview: Overview
  monthly_trend: TrendPoint[]
  club_ranking: RankingItem[]
  college_ranking: RankingItem[]
  category_distribution: CategoryItem[]
  top_activities: ActivityItem[]
  contexts: {
    terms: ContextOption[]
    campuses: ContextOption[]
  }
}
