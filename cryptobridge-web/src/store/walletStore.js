import { create } from 'zustand'
import api from '../services/api'

const useWalletStore = create((set) => ({
  balance: null,
  transactions: [],
  depositAddress: null,
  isLoading: false,
  error: null,

  fetchBalance: async () => {
    try {
      const res = await api.get('/wallet/balance')
      set({ balance: res.data.data })
    } catch (err) {
      set({ error: err.response?.data?.error || 'Failed to load balance' })
    }
  },

  fetchDepositAddress: async () => {
    set({ isLoading: true })
    try {
      const res = await api.get('/wallet/deposit-address')
      set({ depositAddress: res.data.data, isLoading: false })
    } catch (err) {
      set({ error: err.response?.data?.error, isLoading: false })
    }
  },

  fetchTransactions: async (page = 1) => {
    set({ isLoading: true })
    try {
      const res = await api.get(`/wallet/transactions?page=${page}`)
      set({ transactions: res.data.data.transactions, isLoading: false })
    } catch {
      set({ isLoading: false })
    }
  },

  simulateDeposit: async (amount) => {
    try {
      const res = await api.post('/wallet/dev/simulate-deposit', { amount })
      return { success: true, data: res.data.data }
    } catch (err) {
      return { success: false, error: err.response?.data?.error }
    }
  },
}))

export default useWalletStore
