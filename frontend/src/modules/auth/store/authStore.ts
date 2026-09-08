// Auth Store - Zustand
import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { UserPublic, TokenResponse } from '@/types/api'

interface AuthState {
  user: UserPublic | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (tokens: TokenResponse, user: UserPublic) => void
  logout: () => void
  setTokens: (tokens: TokenResponse) => void
  setUser: (user: UserPublic) => void
  hydrate: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,

      login: (tokens, user) => set({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        user,
        isAuthenticated: true,
      }),

      logout: () => set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
      }),

      setTokens: (tokens) => set({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
      }),

      setUser: (user) => set({ user }),

      hydrate: () => {
        // Zustand persist ya hidrata automáticamente
        // Esta función existe para compatibilidad con el hook useAuth
        const state = get()
        if (state.accessToken && state.user) {
          set({ isAuthenticated: true })
        }
      },
    }),
    {
      name: 'geoforraje-auth',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)