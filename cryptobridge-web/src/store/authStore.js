import { create } from 'zustand'
import api from '../services/api'

const useAuthStore = create((set, get) => ({
  user: null,
  isLoading: false,
  isAuthenticated: false,
  error: null,

  init: async () => {
    const token = localStorage.getItem('access_token')
    if (!token) return
    try {
      set({ isLoading: true })
      const res = await api.get('/auth/me')
      set({ user: res.data.data, isAuthenticated: true, isLoading: false })
    } catch {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      set({ user: null, isAuthenticated: false, isLoading: false })
    }
  },

  register: async (phone, password, fullName, language) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.post('/auth/register', {
        phone, password, full_name: fullName, language
      })
      set({ isLoading: false })
      return { success: true, data: res.data.data }
    } catch (err) {
      const msg = err.response?.data?.error || 'Registration failed'
      set({ error: msg, isLoading: false })
      return { success: false, error: msg }
    }
  },

  verifyOTP: async (phone, otp) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.post('/auth/verify-otp', { phone, otp })
      const { access_token, refresh_token, user } = res.data.data
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
      set({ user, isAuthenticated: true, isLoading: false })
      return { success: true }
    } catch (err) {
      const msg = err.response?.data?.error || 'OTP verification failed'
      set({ error: msg, isLoading: false })
      return { success: false, error: msg }
    }
  },

  login: async (phone, password) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.post('/auth/login', { phone, password })
      const { access_token, refresh_token, user } = res.data.data
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
      set({ user, isAuthenticated: true, isLoading: false })
      return { success: true }
    } catch (err) {
      const msg = err.response?.data?.error || 'Login failed'
      set({ error: msg, isLoading: false })
      return { success: false, error: msg }
    }
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null, isAuthenticated: false, error: null })
    window.location.href = '/login'
  },

  updateUser: (updates) => set((state) => ({
    user: { ...state.user, ...updates }
  })),

  clearError: () => set({ error: null }),
}))

export default useAuthStore
