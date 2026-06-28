import { create } from 'zustand'
import { User } from '../types/auth'

interface AuthState {
  // In-memory only — never written to localStorage or sessionStorage.
  // Page refresh logs the user out. This is the security requirement.
  token: string | null
  user: User | null
  setAuth: (token: string, user: User) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  setAuth: (token, user) => set({ token, user }),
  clearAuth: () => set({ token: null, user: null }),
}))