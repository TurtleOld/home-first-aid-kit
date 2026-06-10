<script setup>
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
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
  </section>
</template>
