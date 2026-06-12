<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api/client'
import { formatDateTime } from '../utils/expiry'

const invitations = ref([])
const isLoading = ref(true)
const isCreating = ref(false)
const error = ref('')
const copiedId = ref(null)

const members = ref([])
const membersError = ref('')
const resetState = reactive({})

async function loadInvitations() {
  isLoading.value = true
  error.value = ''
  try {
    invitations.value = await api.get('/invitations')
  } catch (requestError) {
    error.value = requestError.message || 'Не удалось загрузить приглашения'
  } finally {
    isLoading.value = false
  }
}

async function loadMembers() {
  membersError.value = ''
  try {
    members.value = await api.get('/members')
  } catch (requestError) {
    membersError.value = requestError.message || 'Не удалось загрузить список участников'
  }
}

function resetFormFor(userId) {
  if (!resetState[userId]) {
    resetState[userId] = { open: false, password: '', error: '', notice: '', isSaving: false }
  }
  return resetState[userId]
}

function toggleResetForm(userId) {
  const state = resetFormFor(userId)
  state.open = !state.open
  state.password = ''
  state.error = ''
  state.notice = ''
}

async function resetMemberPassword(userId) {
  const state = resetFormFor(userId)
  state.error = ''
  state.notice = ''

  if (state.password.length < 8) {
    state.error = 'Пароль должен содержать не менее 8 символов.'
    return
  }

  state.isSaving = true
  try {
    await api.post(`/members/${userId}/password`, { new_password: state.password })
    state.notice = 'Пароль обновлён.'
    state.password = ''
  } catch (requestError) {
    state.error = requestError.message || 'Не удалось сменить пароль'
  } finally {
    state.isSaving = false
  }
}

async function createInvitation() {
  isCreating.value = true
  error.value = ''
  try {
    const created = await api.post('/invitations', {})
    invitations.value = [created, ...invitations.value]
    await copyLink(created)
  } catch (requestError) {
    error.value = requestError.message || 'Не удалось создать приглашение'
  } finally {
    isCreating.value = false
  }
}

// invite_url с бэка указывает на хост API; собираем ссылку от текущего origin SPA.
function inviteLink(invitation) {
  return `${window.location.origin}/invite/${invitation.token}`
}

async function copyLink(invitation) {
  try {
    await navigator.clipboard.writeText(inviteLink(invitation))
    copiedId.value = invitation.id
    setTimeout(() => {
      if (copiedId.value === invitation.id) {
        copiedId.value = null
      }
    }, 2500)
  } catch {
    error.value = 'Не удалось скопировать — выделите ссылку вручную.'
  }
}

async function revoke(invitation) {
  if (!window.confirm('Отозвать приглашение? Ссылка перестанет работать.')) {
    return
  }

  error.value = ''
  try {
    await api.delete(`/invitations/${invitation.id}`)
    invitations.value = invitations.value.filter((item) => item.id !== invitation.id)
  } catch (requestError) {
    error.value = requestError.message || 'Не удалось отозвать приглашение'
  }
}

onMounted(() => {
  loadInvitations()
  loadMembers()
})
</script>

<template>
  <section class="page-section">
    <div class="section-header">
      <div>
        <p class="eyebrow">Администрирование</p>
        <h1>Приглашения</h1>
      </div>
      <button
        class="primary-button inline-button"
        type="button"
        :disabled="isCreating"
        @click="createInvitation"
      >
        {{ isCreating ? 'Создаём...' : '+ Новая ссылка' }}
      </button>
    </div>

    <p class="muted">
      Создайте ссылку и отправьте её члену семьи: перейдя по ней, он зарегистрируется и попадёт в
      вашу аптечку. Каждая ссылка одноразовая.
    </p>

    <p v-if="error" class="form-error">{{ error }}</p>
    <p v-if="isLoading" class="muted">Загружаем приглашения...</p>

    <ul v-else-if="invitations.length" class="invitation-list">
      <li v-for="invitation in invitations" :key="invitation.id" class="invitation-card">
        <div class="invitation-info">
          <code class="invitation-link">{{ inviteLink(invitation) }}</code>
          <span class="invitation-meta muted">
            создано {{ formatDateTime(invitation.created_at) }} · действует до
            {{ formatDateTime(invitation.expires_at) }}
          </span>
        </div>
        <div class="invitation-actions">
          <button class="text-button" type="button" @click="copyLink(invitation)">
            {{ copiedId === invitation.id ? '✓ Скопировано' : 'Копировать' }}
          </button>
          <button class="text-button danger-button" type="button" @click="revoke(invitation)">
            Отозвать
          </button>
        </div>
      </li>
    </ul>

    <div v-else class="empty-state">
      <h2>Активных приглашений нет</h2>
      <p>Нажмите «Новая ссылка», чтобы пригласить члена семьи.</p>
    </div>

    <h2>Участники семьи</h2>
    <p v-if="membersError" class="form-error">{{ membersError }}</p>

    <ul v-if="members.length" class="invitation-list">
      <li v-for="member in members" :key="member.user.id" class="invitation-card">
        <div class="invitation-info">
          <span>{{ member.user.username }}</span>
          <span class="invitation-meta muted">
            {{ member.role === 'admin' ? 'Администратор' : 'Участник' }}
          </span>
        </div>
        <div class="invitation-actions">
          <button class="text-button" type="button" @click="toggleResetForm(member.user.id)">
            Сбросить пароль
          </button>
        </div>

        <form
          v-if="resetState[member.user.id]?.open"
          class="medicine-form"
          @submit.prevent="resetMemberPassword(member.user.id)"
        >
          <label>
            Новый пароль
            <input
              v-model="resetState[member.user.id].password"
              type="password"
              autocomplete="new-password"
              minlength="8"
              required
            />
          </label>
          <p v-if="resetState[member.user.id].error" class="form-error">
            {{ resetState[member.user.id].error }}
          </p>
          <p v-if="resetState[member.user.id].notice" class="form-notice" role="status">
            {{ resetState[member.user.id].notice }}
          </p>
          <div class="form-actions">
            <button
              class="primary-button inline-button"
              type="submit"
              :disabled="resetState[member.user.id].isSaving"
            >
              {{ resetState[member.user.id].isSaving ? 'Сохраняем...' : 'Сохранить новый пароль' }}
            </button>
          </div>
        </form>
      </li>
    </ul>
  </section>
</template>
