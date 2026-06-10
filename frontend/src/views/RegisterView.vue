<script setup>
import { onMounted, reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

onMounted(async () => {
  try {
    const status = await api.get('/auth/registration-status', { skipAuthRetry: true })
    if (!status?.open) {
      router.replace({ name: 'login' })
    }
  } catch {
    // Статус неизвестен — оставляем форму, бэкенд всё равно отклонит лишнюю регистрацию
  }
})

const form = reactive({
  username: '',
  password: '',
  family_name: '',
  email: '',
  first_name: '',
  last_name: ''
})
const error = ref('')

async function submit() {
  error.value = ''

  try {
    await auth.register(form)
    router.push('/medicines')
  } catch (requestError) {
    error.value = requestError.message || 'Не удалось зарегистрироваться'
  }
}
</script>

<template>
  <section class="auth-page">
    <form class="auth-panel auth-panel-wide" @submit.prevent="submit">
      <div>
        <p class="eyebrow">Регистрация</p>
        <h1>Создать семью</h1>
      </div>

      <div class="form-grid">
        <label>
          Имя пользователя
          <input v-model.trim="form.username" autocomplete="username" required />
        </label>

        <label>
          Название семьи
          <input v-model.trim="form.family_name" required />
        </label>

        <label>
          Пароль
          <input v-model="form.password" type="password" autocomplete="new-password" minlength="8" required />
        </label>

        <label>
          Email
          <input v-model.trim="form.email" type="email" autocomplete="email" />
        </label>

        <label>
          Имя
          <input v-model.trim="form.first_name" autocomplete="given-name" />
        </label>

        <label>
          Фамилия
          <input v-model.trim="form.last_name" autocomplete="family-name" />
        </label>
      </div>

      <p v-if="error" class="form-error">{{ error }}</p>

      <button class="primary-button" type="submit" :disabled="auth.isLoading">
        {{ auth.isLoading ? 'Создаём...' : 'Создать аккаунт' }}
      </button>

      <p class="muted">
        Уже есть аккаунт?
        <RouterLink to="/login">Войти</RouterLink>
      </p>
    </form>
  </section>
</template>
