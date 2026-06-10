import { defineStore } from 'pinia'

const THEME_STORAGE_KEY = 'hfk-theme-mode'
const MODES = ['system', 'light', 'dark']

export const useThemeStore = defineStore('theme', {
  state: () => ({
    mode: 'system',
    resolvedTheme: 'light',
    mediaQuery: null
  }),

  getters: {
    modeLabel: (state) => {
      const labels = {
        system: 'Системная',
        light: 'Светлая',
        dark: 'Тёмная'
      }
      return labels[state.mode]
    }
  },

  actions: {
    init() {
      const savedMode = localStorage.getItem(THEME_STORAGE_KEY)
      this.mode = MODES.includes(savedMode) ? savedMode : 'system'
      this.mediaQuery = window.matchMedia?.('(prefers-color-scheme: dark)') || null

      this.applyTheme()
      this.mediaQuery?.addEventListener('change', this.handleSystemThemeChange)
    },

    handleSystemThemeChange() {
      if (this.mode === 'system') {
        this.applyTheme()
      }
    },

    resolveTheme() {
      if (this.mode === 'dark') {
        return 'dark'
      }

      if (this.mode === 'system' && this.mediaQuery?.matches) {
        return 'dark'
      }

      return 'light'
    },

    applyTheme() {
      this.resolvedTheme = this.resolveTheme()
      document.documentElement.dataset.theme = this.resolvedTheme
      document.documentElement.dataset.themeMode = this.mode
    },

    setMode(mode) {
      this.mode = MODES.includes(mode) ? mode : 'system'
      localStorage.setItem(THEME_STORAGE_KEY, this.mode)
      this.applyTheme()
    },

    cycleMode() {
      const nextIndex = (MODES.indexOf(this.mode) + 1) % MODES.length
      this.setMode(MODES[nextIndex])
    }
  }
})
