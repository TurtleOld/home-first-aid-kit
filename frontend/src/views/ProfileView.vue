<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'
import { getPushSubscription, isPushSupported, subscribeToPush, unsubscribeFromPush } from '../utils/push'

const auth = useAuthStore()
const router = useRouter()

const form = reactive({
  current_password: '',
  new_password: '',
  new_password_repeat: ''
})

const isSaving = ref(false)
const error = ref('')
const notice = ref('')

const pushSupported = ref(isPushSupported())
const pushSubscribed = ref(false)
const pushBusy = ref(false)
const pushError = ref('')

onMounted(async () => {
  if (!pushSupported.value) {
    return
  }
  try {
    pushSubscribed.value = Boolean(await getPushSubscription())
  } catch {
    pushSupported.value = false
  }
})

async function togglePush() {
  pushError.value = ''
  pushBusy.value = true
  try {
    if (pushSubscribed.value) {
      await unsubscribeFromPush()
      pushSubscribed.value = false
    } else {
      await subscribeToPush()
      pushSubscribed.value = true
    }
  } catch (requestError) {
    pushError.value = requestError.message || 'Не удалось изменить настройки уведомлений'
  } finally {
    pushBusy.value = false
  }
}

async function changePassword() {
  error.value = ''
  notice.value = ''

  if (form.new_password.length < 8) {
    error.value = 'Новый пароль должен содержать не менее 8 символов.'
    return
  }
  if (form.new_password !== form.new_password_repeat) {
    error.value = 'Пароли не совпадают.'
    return
  }

  isSaving.value = true
  try {
    await api.post('/auth/password', {
      current_password: form.current_password,
      new_password: form.new_password
    })
    auth.logout()
    router.push({ name: 'login', query: { passwordChanged: '1' } })
  } catch (requestError) {
    error.value = requestError.message || 'Не удалось изменить пароль'
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <section class="page-section">
    <div class="section-header">
      <div>
        <p class="eyebrow">Профиль</p>
        <h1>{{ auth.displayName }}</h1>
      </div>
    </div>

    <dl class="profile-list">
      <div>
        <dt>Логин</dt>
        <dd>{{ auth.user?.username }}</dd>
      </div>
      <div>
        <dt>Email</dt>
        <dd>{{ auth.user?.email || 'Не указан' }}</dd>
      </div>
      <div>
        <dt>Семья</dt>
        <dd>{{ auth.family?.name }}</dd>
      </div>
      <div>
        <dt>Роль</dt>
        <dd>{{ auth.role === 'admin' ? 'Администратор' : 'Участник' }}</dd>
      </div>
    </dl>

    <h2>Уведомления</h2>
    <div v-if="pushSupported" class="profile-push">
      <p>
        {{
          pushSubscribed
            ? 'Push-уведомления о просрочке и заканчивающихся лекарствах включены.'
            : 'Включите push-уведомления, чтобы получать напоминания о просрочке и заканчивающихся лекарствах.'
        }}
      </p>
      <p v-if="pushError" class="form-error">{{ pushError }}</p>
      <div class="form-actions">
        <button class="primary-button inline-button" type="button" :disabled="pushBusy" @click="togglePush">
          {{ pushBusy ? 'Подождите...' : pushSubscribed ? 'Отключить уведомления' : 'Включить уведомления' }}
        </button>
      </div>
    </div>
    <p v-else class="form-notice">Push-уведомления не поддерживаются этим браузером.</p>

    <h2>Смена пароля</h2>
    <form class="medicine-form" @submit.prevent="changePassword">
      <div class="form-grid">
        <label>
          Текущий пароль
          <input v-model="form.current_password" type="password" autocomplete="current-password" required />
        </label>
        <label>
          Новый пароль
          <input v-model="form.new_password" type="password" autocomplete="new-password" required minlength="8" />
        </label>
        <label>
          Повторите новый пароль
          <input
            v-model="form.new_password_repeat"
            type="password"
            autocomplete="new-password"
            required
            minlength="8"
          />
        </label>
      </div>

      <p v-if="error" class="form-error">{{ error }}</p>
      <p v-if="notice" class="form-notice" role="status">{{ notice }}</p>

      <div class="form-actions">
        <button class="primary-button inline-button" type="submit" :disabled="isSaving">
          {{ isSaving ? 'Сохраняем...' : 'Сменить пароль' }}
        </button>
      </div>
    </form>
  </section>
</template>
