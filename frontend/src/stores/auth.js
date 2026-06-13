import { defineStore } from 'pinia'
import { api, configureApiAuth } from '../api/client'

const ACCESS_TOKEN_KEY = 'hfk-access-token'
const REFRESH_TOKEN_KEY = 'hfk-refresh-token'

function profileFromAuthResponse(payload) {
  return {
    user: payload.user || null,
    family: payload.family || null,
    role: payload.role || null
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: null,
    refreshToken: null,
    user: null,
    family: null,
    role: null,
    isBootstrapped: false,
    isLoading: false
  }),

  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken && state.user),
    isAdmin: (state) => state.role === 'admin',
    displayName: (state) => {
      if (!state.user) {
        return ''
      }

      const fullName = [state.user.first_name, state.user.last_name].filter(Boolean).join(' ')
      return fullName || state.user.username
    }
  },

  actions: {
    init() {
      this.accessToken = localStorage.getItem(ACCESS_TOKEN_KEY)
      this.refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
      configureApiAuth({
        getAccessToken: () => this.accessToken,
        getRefreshToken: () => this.refreshToken,
        refreshAccessToken: () => this.refreshAccessToken()
      })
    },

    setTokens({ access, refresh }) {
      this.accessToken = access || this.accessToken
      this.refreshToken = refresh || this.refreshToken

      if (access) {
        localStorage.setItem(ACCESS_TOKEN_KEY, access)
      }
      if (refresh) {
        localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
      }
    },

    setProfile(profile) {
      this.user = profile.user
      this.family = profile.family
      this.role = profile.role
    },

    applyAuthResponse(payload) {
      this.setTokens(payload)
      this.setProfile(profileFromAuthResponse(payload))
    },

    async bootstrap() {
      if (this.isBootstrapped) {
        return
      }

      if (!this.accessToken) {
        this.isBootstrapped = true
        return
      }

      try {
        await this.fetchMe()
      } catch {
        this.logout()
      } finally {
        this.isBootstrapped = true
      }
    },

    async fetchMe() {
      const profile = await api.get('/auth/me')
      this.setProfile(profile)
      return profile
    },

    async login(credentials) {
      this.isLoading = true
      try {
        const tokens = await api.post('/auth/login', credentials, { skipAuthRetry: true })
        this.setTokens(tokens)
        await this.fetchMe()
      } finally {
        this.isLoading = false
      }
    },

    async register(payload) {
      this.isLoading = true
      try {
        const response = await api.post('/auth/register', payload, { skipAuthRetry: true })
        this.applyAuthResponse(response)
      } finally {
        this.isLoading = false
      }
    },

    async acceptInvitation(token, payload) {
      this.isLoading = true
      try {
        const response = await api.post(`/invitations/${token}/accept`, payload, {
          skipAuthRetry: true
        })
        this.applyAuthResponse(response)
      } finally {
        this.isLoading = false
      }
    },

    async refreshAccessToken() {
      if (!this.refreshToken) {
        this.logout()
        return false
      }

      try {
        const response = await api.rawRequest(
          '/auth/refresh',
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh: this.refreshToken })
          },
          null
        )
        this.setTokens({ access: response.access, refresh: response.refresh })
        return true
      } catch {
        this.logout()
        return false
      }
    },

    logout() {
      const refresh = this.refreshToken
      const access = this.accessToken

      this.accessToken = null
      this.refreshToken = null
      this.user = null
      this.family = null
      this.role = null
      localStorage.removeItem(ACCESS_TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)

      if (refresh && access) {
        api
          .rawRequest(
            '/auth/logout',
            {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ refresh })
            },
            access
          )
          .catch(() => {})
      }
    }
  }
})
