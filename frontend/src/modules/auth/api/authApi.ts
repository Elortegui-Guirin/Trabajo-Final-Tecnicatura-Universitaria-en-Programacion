// Auth API Client
import axios from 'axios'
import type { 
  UserRegister, UserLogin, TokenResponse, TokenRefresh, UserPublic,
  VerifyEmailRequest, ResendVerificationRequest,
  ForgotPasswordRequest, ResetPasswordRequest, AuthMessageResponse
} from '@/types/api'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

// Interceptor para adjuntar access token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('geoforraje-auth') 
    ? JSON.parse(localStorage.getItem('geoforraje-auth')!).state.accessToken 
    : null
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Interceptor para refresh token automático
let isRefreshing = false
let failedQueue: Array<{ resolve: (v: string) => void; reject: (e: Error) => void }> = []

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error)
    else resolve(token!)
  })
  failedQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return api(originalRequest)
        }).catch((err) => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const refreshToken = JSON.parse(localStorage.getItem('geoforraje-auth')!).state.refreshToken
        const { data } = await axios.post<TokenResponse>(
          `${import.meta.env.VITE_API_BASE_URL}/auth/refresh`,
          { refresh_token: refreshToken }
        )
        
        // Actualizar store
        const authData = JSON.parse(localStorage.getItem('geoforraje-auth')!)
        authData.state.accessToken = data.access_token
        authData.state.refreshToken = data.refresh_token
        localStorage.setItem('geoforraje-auth', JSON.stringify(authData))
        
        processQueue(null, data.access_token)
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`
        return api(originalRequest)
      } catch (err) {
        processQueue(err as Error, null)
        // Logout automático
        localStorage.removeItem('geoforraje-auth')
        window.location.href = '/login'
        return Promise.reject(err)
      } finally {
        isRefreshing = false
      }
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  register: (data: UserRegister) => api.post<UserPublic>('/auth/register', data),
  login: (data: UserLogin) => api.post<TokenResponse>('/auth/login', data),
  refresh: (data: TokenRefresh) => api.post<TokenResponse>('/auth/refresh', data),
  me: () => api.get<UserPublic>('/auth/me'),
  
  // Nuevos endpoints Fase 2
  verifyEmail: (data: VerifyEmailRequest) => api.post<AuthMessageResponse>('/auth/verify-email', data),
  resendVerification: (data: ResendVerificationRequest) => api.post<AuthMessageResponse>('/auth/resend-verification', data),
  forgotPassword: (data: ForgotPasswordRequest) => api.post<AuthMessageResponse>('/auth/forgot-password', data),
  resetPassword: (data: ResetPasswordRequest) => api.post<AuthMessageResponse>('/auth/reset-password', data),
  logout: () => api.post<AuthMessageResponse>('/auth/logout'),
}

export default api