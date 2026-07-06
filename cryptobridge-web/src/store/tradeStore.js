import { create } from 'zustand'
import api from '../services/api'

const useTradeStore = create((set, get) => ({
  activeTrade: null,
  trades: [],
  isLoading: false,
  error: null,

  createTrade: async (usdtAmount, rateXaf, paymentMethod) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.post('/trades/create', {
        usdt_amount: usdtAmount,
        rate_xaf_per_usdt: rateXaf,
        payment_method: paymentMethod,
      })
      set({ activeTrade: res.data.data.trade, isLoading: false })
      return { success: true, data: res.data.data }
    } catch (err) {
      const msg = err.response?.data?.error || 'Failed to create trade'
      set({ error: msg, isLoading: false })
      return { success: false, error: msg }
    }
  },

  joinTrade: async (tradeCode, buyerPhone) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.post('/trades/join', {
        trade_code: tradeCode,
        buyer_phone: buyerPhone,
      })
      set({ activeTrade: res.data.data.trade, isLoading: false })
      return { success: true, data: res.data.data }
    } catch (err) {
      const msg = err.response?.data?.error || 'Failed to join trade'
      set({ error: msg, isLoading: false })
      return { success: false, error: msg }
    }
  },

  getTrade: async (tradeId) => {
    try {
      const res = await api.get(`/trades/${tradeId}`)
      set({ activeTrade: res.data.data })
      return res.data.data
    } catch (err) {
      return null
    }
  },

  fetchMyTrades: async (page = 1, role = 'all') => {
    set({ isLoading: true })
    try {
      const res = await api.get(`/trades/my/list?page=${page}&role=${role}`)
      set({ trades: res.data.data.trades, isLoading: false })
      return res.data.data
    } catch {
      set({ isLoading: false })
    }
  },

  cancelTrade: async (tradeId) => {
    try {
      const res = await api.post(`/trades/${tradeId}/cancel`)
      set({ activeTrade: null })
      return { success: true, data: res.data.data }
    } catch (err) {
      return { success: false, error: err.response?.data?.error }
    }
  },

  simulatePayment: async (tradeId) => {
    try {
      const res = await api.post(`/trades/${tradeId}/dev/simulate-payment`)
      set({ activeTrade: res.data.data.trade })
      return { success: true, data: res.data.data }
    } catch (err) {
      return { success: false, error: err.response?.data?.error }
    }
  },

  clearActiveTrade: () => set({ activeTrade: null }),
  clearError: () => set({ error: null }),
}))

export default useTradeStore
