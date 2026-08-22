export type UserRole = 'admin' | 'club_manager' | 'student'

export interface CurrentUser {
  id: number
  username: string
  role: UserRole
  student_id: number | null
}

export interface LoginResponse {
  access_token: string
  token_type: 'bearer'
  expires_at: string
  user: CurrentUser
}
