import { create } from 'zustand'
import { User } from '../types/auth'
import { useChatStore } from './chatStore'
import { useFileStore } from './fileStore'

interface AuthState {
  // In-memory only — never written to localStorage or sessionStorage.
  // Page refresh logs the user out. This is the security requirement.
  token: string | null
  user: User | null
  setAuth: (token: string, user: User) => void
  clearAuth: () => void
}

/**
 * Wipes every store that holds account-scoped data.
 * Called from both setAuth and clearAuth — see comments below for why
 * it's in both places, not just one.
 *
 * If a new store holding per-account data gets added to this app later,
 * add its reset() call here too, or this bug comes back for that store.
 */
function resetAccountScopedStores(): void {
  useChatStore.getState().reset()
  useFileStore.getState().reset()
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,

  setAuth: (token, user) => {
    // Defensive, not strictly required to fix the reported bug: guarantees
    // a freshly logged-in session never inherits leftover state even if
    // some future code path sets a new token without calling clearAuth first.
    resetAccountScopedStores()
    set({ token, user })
  },

  clearAuth: () => {
    // Required fix. This must run on every logout, from every trigger —
    // the explicit logout button AND the axios 401 interceptor. Putting
    // the reset here, instead of at each call site that triggers a logout,
    // means it fires automatically no matter what calls clearAuth().
    resetAccountScopedStores()
    set({ token: null, user: null })
  },
}))