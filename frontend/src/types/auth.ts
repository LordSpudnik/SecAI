export interface User {
  id: string
  email: string
  full_name: string
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}