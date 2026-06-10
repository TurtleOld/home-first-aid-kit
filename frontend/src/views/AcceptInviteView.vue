<script setup>
import { onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const token = route.params.token
const invitation = ref(null)
const isLoadingInvitation = ref(true)
const error = ref('')
const form = reactive({
  username: '',
  password: '',
  email: '',
  first_name: '',
  last_name: ''
})

onMounted(async () => {
  try {
    invitation.value = await api.get(`/invitations/${token}`, { skipAuthRetry: true })
    if (!invitation.value.is_valid) {
      error.value = 'Приглашение недействительно или истекло.'
    }
  } catch (requestError) {
    error.value = requestError.message || 'Не удалось проверить приглашение'
  } finally {
    isLoadingInvitation.value = false
  }
})

async function submit() {
  error.value = ''

  try {
    await auth.acceptInvitation(token, form)
    router.push('/medicines')
  } catch (requestError) {
    error.value = requestError.message || 'Не удалось принять приглашение'
  }
}
</script>

<template>
  <section class="auth-page">
    <form class="auth-panel auth-panel-wide" @submit.prevent="submit">
      <div>
        <p class="eyebrow">Приглашение</p>
        <h1>Присоединиться к семье</h1>
        <p v-if="invitation?.family" class="muted">
          Вы принимаете приглашение в «{{ invitation.family.name }}».
        </p>
        <p v-else-if="isLoadingInvitation" class="muted">Проверяем ссылку...</p>
      </div>

      <div class="form-grid">
        <label>
          Имя пользователя
          <input v-model.trim="form.username" autocomplete="username" required />
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

      <button
        class="primary-button"
        type="submit"
        :disabled="auth.isLoading || isLoadingInvitation || !invitation?.is_valid"
      >
        {{ auth.isLoading ? 'Подключаем...' : 'Принять приглашение' }}
      </button>

      <p class="muted">
        Уже есть аккаунт?
        <RouterLink to="/login">Войти</RouterLink>
      </p>
    </form>
  </section>
</template>
