import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from './auth'
import { api, configureApiAuth } from '../api/client'

vi.mock('../api/client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    rawRequest: vi.fn()
  },
  configureApiAuth: vi.fn()
}))

describe('auth store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  describe('init', () => {
    it('restores tokens from localStorage and configures the API client', () => {
      localStorage.setItem('hfk-access-token', 'access-1')
      localStorage.setItem('hfk-refresh-token', 'refresh-1')

      const store = useAuthStore()
      store.init()

      expect(store.accessToken).toBe('access-1')
      expect(store.refreshToken).toBe('refresh-1')
      expect(configureApiAuth).toHaveBeenCalledWith(
        expect.objectContaining({
          getAccessToken: expect.any(Function),
          getRefreshToken: expect.any(Function),
          refreshAccessToken: expect.any(Function)
        })
      )
    })
  })

  describe('login', () => {
    it('stores tokens and profile on success', async () => {
      api.post.mockResolvedValue({ access: 'access-1', refresh: 'refresh-1' })
      api.get.mockResolvedValue({
        user: { username: 'alex' },
        family: { id: 1, name: 'Family' },
        role: 'admin'
      })

      const store = useAuthStore()
      await store.login({ username: 'alex', password: 'secret' })

      expect(api.post).toHaveBeenCalledWith(
        '/auth/login',
        { username: 'alex', password: 'secret' },
        { skipAuthRetry: true }
      )
      expect(store.accessToken).toBe('access-1')
      expect(store.refreshToken).toBe('refresh-1')
      expect(localStorage.getItem('hfk-access-token')).toBe('access-1')
      expect(localStorage.getItem('hfk-refresh-token')).toBe('refresh-1')
      expect(store.user).toEqual({ username: 'alex' })
      expect(store.role).toBe('admin')
      expect(store.isAuthenticated).toBe(true)
      expect(store.isLoading).toBe(false)
    })

    it('resets isLoading even when the request fails', async () => {
      api.post.mockRejectedValue(new Error('bad credentials'))

      const store = useAuthStore()
      await expect(store.login({ username: 'alex', password: 'wrong' })).rejects.toThrow(
        'bad credentials'
      )

      expect(store.isLoading).toBe(false)
      expect(store.isAuthenticated).toBe(false)
    })
  })

  describe('refreshAccessToken', () => {
    it('updates the access token on success', async () => {
      const store = useAuthStore()
      store.setTokens({ access: 'old-access', refresh: 'refresh-1' })
      api.rawRequest.mockResolvedValue({ access: 'new-access' })

      const result = await store.refreshAccessToken()

      expect(result).toBe(true)
      expect(store.accessToken).toBe('new-access')
      expect(localStorage.getItem('hfk-access-token')).toBe('new-access')
      expect(api.rawRequest).toHaveBeenCalledWith(
        '/auth/refresh',
        expect.objectContaining({ method: 'POST' }),
        null
      )
    })

    it('logs out when there is no refresh token', async () => {
      const store = useAuthStore()
      store.setTokens({ access: 'old-access', refresh: 'refresh-1' })
      store.refreshToken = null

      const result = await store.refreshAccessToken()

      expect(result).toBe(false)
      expect(store.accessToken).toBeNull()
      expect(localStorage.getItem('hfk-access-token')).toBeNull()
    })

    it('logs out when the refresh request fails', async () => {
      const store = useAuthStore()
      store.setTokens({ access: 'old-access', refresh: 'refresh-1' })
      api.rawRequest.mockRejectedValue(new Error('expired'))

      const result = await store.refreshAccessToken()

      expect(result).toBe(false)
      expect(store.accessToken).toBeNull()
      expect(store.refreshToken).toBeNull()
      expect(localStorage.getItem('hfk-access-token')).toBeNull()
      expect(localStorage.getItem('hfk-refresh-token')).toBeNull()
    })
  })

  describe('logout', () => {
    it('clears state and notifies the backend when tokens are present', () => {
      api.rawRequest.mockResolvedValue(null)

      const store = useAuthStore()
      store.setTokens({ access: 'access-1', refresh: 'refresh-1' })
      store.setProfile({ user: { username: 'alex' }, family: { id: 1 }, role: 'admin' })

      store.logout()

      expect(store.accessToken).toBeNull()
      expect(store.refreshToken).toBeNull()
      expect(store.user).toBeNull()
      expect(store.family).toBeNull()
      expect(store.role).toBeNull()
      expect(localStorage.getItem('hfk-access-token')).toBeNull()
      expect(localStorage.getItem('hfk-refresh-token')).toBeNull()
      expect(api.rawRequest).toHaveBeenCalledWith(
        '/auth/logout',
        expect.objectContaining({ method: 'POST' }),
        'access-1'
      )
    })

    it('does not call the backend when there are no tokens', () => {
      const store = useAuthStore()

      store.logout()

      expect(api.rawRequest).not.toHaveBeenCalled()
    })
  })
})
