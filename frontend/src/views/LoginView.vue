<script setup>
import { onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const form = reactive({
  username: '',
  password: ''
})
const error = ref('')
const registrationOpen = ref(false)

onMounted(async () => {
  try {
    const status = await api.get('/auth/registration-status', { skipAuthRetry: true })
    registrationOpen.value = Boolean(status?.open)
  } catch {
    registrationOpen.value = false
  }
})

async function submit() {
  error.value = ''

  try {
    await auth.login(form)
    router.push(route.query.redirect?.toString() || '/medicines')
  } catch (requestError) {
    error.value = requestError.message || 'Не удалось войти'
  }
}
</script>

<template>
  <section class="auth-page">
    <form class="auth-panel" @submit.prevent="submit">
      <div>
        <p class="eyebrow">Вход</p>
        <h1>Войти в аптечку</h1>
      </div>

      <label>
        Имя пользователя
        <input v-model.trim="form.username" autocomplete="username" required />
      </label>

      <label>
        Пароль
        <input v-model="form.password" type="password" autocomplete="current-password" required />
      </label>

      <p v-if="error" class="form-error">{{ error }}</p>

      <button class="primary-button" type="submit" :disabled="auth.isLoading">
        {{ auth.isLoading ? 'Входим...' : 'Войти' }}
      </button>

      <p v-if="registrationOpen" class="muted">
        Нет семьи?
        <RouterLink to="/register">Зарегистрировать администратора</RouterLink>
      </p>
    </form>
  </section>
</template>
