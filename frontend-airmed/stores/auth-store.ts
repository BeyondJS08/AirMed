import { create } from "zustand"
import type { User } from "@/types"
import * as authService from "@/services/auth"

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean

  login: (email: string, password: string) => Promise<void>
  register: (data: {
    email: string
    password: string
    full_name?: string
    is_professional?: boolean
  }) => Promise<void>
  logout: () => void
  setTokens: (access: string, refresh: string) => void
  hydrate: () => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,

  login: async (email: string, password: string) => {
    const res = await authService.login(email, password)
    localStorage.setItem("accessToken", res.access_token)
    localStorage.setItem("refreshToken", res.refresh_token)
    set({
      accessToken: res.access_token,
      refreshToken: res.refresh_token,
    })
    const user = await authService.getCurrentUser(res.access_token)
    set({ user, isAuthenticated: true })
  },

  register: async (data) => {
    await authService.register(data)
  },

  logout: () => {
    localStorage.removeItem("accessToken")
    localStorage.removeItem("refreshToken")
    set({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
    })
  },

  setTokens: (access: string, refresh: string) => {
    localStorage.setItem("accessToken", access)
    localStorage.setItem("refreshToken", refresh)
    set({ accessToken: access, refreshToken: refresh, isAuthenticated: true })
  },

  hydrate: () => {
    const accessToken = localStorage.getItem("accessToken")
    if (!accessToken) return
    set({ accessToken, isAuthenticated: true })
    authService
      .getCurrentUser(accessToken)
      .then((user) => {
        set({ user, isAuthenticated: true })
      })
      .catch(() => {
        const refreshToken = localStorage.getItem("refreshToken")
        if (refreshToken) {
          authService
            .refresh(refreshToken)
            .then((res) => {
              localStorage.setItem("accessToken", res.access_token)
              localStorage.setItem("refreshToken", res.refresh_token)
              set({
                accessToken: res.access_token,
                refreshToken: res.refresh_token,
                isAuthenticated: true,
              })
              return authService.getCurrentUser(res.access_token)
            })
            .then((user) => {
              set({ user, isAuthenticated: true })
            })
            .catch(() => {
              get().logout()
            })
        } else {
          get().logout()
        }
      })
  },
}))
