<script setup>
import { computed } from 'vue'
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useThemeStore } from './stores/theme'

const auth = useAuthStore()
const theme = useThemeStore()
const router = useRouter()

const navItems = computed(() => {
  const items = [
    { to: '/medicines', label: 'Аптечка' },
    { to: '/shopping', label: 'Покупки' },
    { to: '/changelog', label: 'Журнал' }
  ]

  if (auth.isAdmin) {
    items.push({ to: '/invitations', label: 'Приглашения' })
  }

  items.push({ to: '/profile', label: 'Профиль' })
  return items
})

function logout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="app-shell">
    <header v-if="auth.isAuthenticated" class="app-header">
      <RouterLink class="brand" to="/medicines" aria-label="Домашняя аптечка">
        <span class="brand-mark" aria-hidden="true">+</span>
        <span>Домашняя аптечка</span>
      </RouterLink>

      <nav class="main-nav" aria-label="Основная навигация">
        <RouterLink v-for="item in navItems" :key="item.to" :to="item.to">
          {{ item.label }}
        </RouterLink>
      </nav>

      <div class="header-actions">
        <button
          class="icon-button"
          type="button"
          :aria-label="`Тема: ${theme.modeLabel}`"
          :title="`Тема: ${theme.modeLabel}`"
          @click="theme.cycleMode()"
        >
          <span v-if="theme.mode === 'light'" aria-hidden="true">☀</span>
          <span v-else-if="theme.mode === 'dark'" aria-hidden="true">☾</span>
          <span v-else aria-hidden="true">◐</span>
        </button>
        <button class="text-button" type="button" @click="logout">Выйти</button>
      </div>
    </header>

    <main class="app-content">
      <RouterView />
    </main>
  </div>
</template>
