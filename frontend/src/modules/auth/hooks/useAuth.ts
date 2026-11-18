// useAuth.ts - Custom hook for auth state
import { authApi } from '@/modules/auth/api/authApi'
import { useEffect, useState } from "react"
import { useAuthStore } from "@/modules/auth/store/authStore"

export function useAuth() {
  const { user, accessToken, refreshToken, isAuthenticated, isLoading, login, logout, refresh } = useAuthStore()

  const [loading, setLoading] = useState(isLoading)

  useEffect(() => {
    setLoading(isLoading)
  }, [isLoading])

  const loginWithUser = (tokens: { access_token: string; refresh_token: string }, user: typeof user | null) => {
    login(tokens, user)
  }

  const logoutWithRedirect = async () => {
    try {
      await authApi.logout() // invalida el refresh token en el servidor
    } catch {
      // ignorar: la sesión local se cierra igual
    }
    logout()
    window.location.href = "/login"
  }

  return {
    user,
    accessToken,
    refreshToken,
    isAuthenticated,
    isLoading: loading,
    login: loginWithUser,
    logout: logoutWithRedirect,
    refresh,
  }
}