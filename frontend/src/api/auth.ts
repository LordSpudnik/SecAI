import client from './client'
import { TokenResponse, User } from '../types/auth'

export const authApi = {
  register: (email: string, password: string, full_name: string) =>
    client.post<{ message: string }>('/auth/register', { email, password, full_name }),

  login: (email: string, password: string) =>
    client.post<TokenResponse>('/auth/login', { email, password }),

  logout: () => client.post<{ message: string }>('/auth/logout'),

  me: () => client.get<User>('/auth/me'),
}