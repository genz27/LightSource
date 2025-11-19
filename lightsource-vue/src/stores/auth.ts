import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import { post, get, put } from '@/api/client'

export interface User {
  id: string
  email: string
  username: string
  role: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('lightsource_access_token') || localStorage.getItem('access_token'))
  const refresh = ref<string | null>(localStorage.getItem('lightsource_refresh_token') || null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!token.value)

  const login = async (email: string, password: string): Promise<boolean> => {
    isLoading.value = true
    error.value = null
    try {
      const resp = await post('/auth/login', { email, password })
      const access = resp?.access_token as string
      const refreshToken = resp?.refresh_token as string
      if (!access) throw new Error('no token')
      token.value = access
      localStorage.setItem('lightsource_access_token', access)
      if (refreshToken) { refresh.value = refreshToken; localStorage.setItem('lightsource_refresh_token', refreshToken) }
      const me = await get('/auth/me')
      user.value = {
        id: me.id,
        email: me.email,
        username: me.username,
        role: me.role,
      }
      return true
    } catch {
      error.value = 'Login failed. Please try again.'
      return false
    } finally {
      isLoading.value = false
    }
  }

  const register = async (email: string, username: string, password: string): Promise<boolean> => {
    isLoading.value = true
    error.value = null
    try {
      await post('/auth/register', { email, username, password })
      return await login(email, password)
    } catch {
      error.value = 'Registration failed. Please try again.'
      return false
    } finally {
      isLoading.value = false
    }
  }

  const logout = () => {
    user.value = null
    token.value = null
    refresh.value = null
    localStorage.removeItem('lightsource_access_token')
    localStorage.removeItem('access_token')
    localStorage.removeItem('lightsource_refresh_token')
  }


  const fetchMe = async (): Promise<void> => {
    if (!token.value) return
    try {
      const me = await get('/auth/me')
      user.value = {
        id: me.id,
        email: me.email,
        username: me.username,
        role: me.role,
      }
    } catch {
      // silently ignore; keep user as null
    }
  }

  const rotateTokens = async (): Promise<boolean> => {
    if (!refresh.value) return false
    try {
      const resp = await post('/auth/refresh', { refresh_token: refresh.value })
      const access = resp?.access_token as string
      const newRefresh = resp?.refresh_token as string
      if (!access) throw new Error('no access token')
      token.value = access
      localStorage.setItem('lightsource_access_token', access)
      if (newRefresh) { refresh.value = newRefresh; localStorage.setItem('lightsource_refresh_token', newRefresh) }
      return true
    } catch {
      return false
    }
  }

  const clearError = () => {
    error.value = null
  }

  const updateProfile = async (payload: Partial<User>): Promise<boolean> => {
    if (!token.value) return false
    try {
      const data = await put('/auth/me', payload)
      user.value = {
        id: data.id ?? user.value?.id ?? '',
        email: data.email ?? payload.email ?? user.value?.email ?? '',
        username: data.username ?? payload.username ?? user.value?.username ?? '',
        role: data.role ?? user.value?.role ?? 'User',
      }
      return true
    } catch {
      return false
    }
  }

  const changePassword = async (current_password: string, new_password: string): Promise<boolean> => {
    if (!token.value) return false
    try {
      await post('/auth/change-password', { current_password, new_password })
      return true
    } catch {
      return false
    }
  }

  return {
    user: readonly(user),
    token: readonly(token),
    refresh: readonly(refresh),
    isLoading: readonly(isLoading),
    error: readonly(error),
    isAuthenticated,
    login,
    register,
    logout,
    fetchMe,
    updateProfile,
    changePassword,
    rotateTokens,
    clearError
  }
})