<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api/client'
import { formatDateTime } from '../utils/expiry'

const items = ref([])
const isLoading = ref(true)
const error = ref('')

const newItem = reactive({ name: '', note: '' })
const isAdding = ref(false)

const pendingItems = computed(() => items.value.filter((item) => !item.is_bought))
const boughtItems = computed(() => items.value.filter((item) => item.is_bought))

async function loadItems() {
  isLoading.value = true
  error.value = ''
  try {
    items.value = await api.get('/shopping-items')
  } catch (requestError) {
    error.value = requestError.message || 'Не удалось загрузить список покупок'
  } finally {
    isLoading.value = false
  }
}

async function addItem() {
  isAdding.value = true
  error.value = ''
  try {
    const created = await api.post('/shopping-items', { ...newItem })
    items.value = [created, ...items.value]
    newItem.name = ''
    newItem.note = ''
  } catch (requestError) {
    error.value = requestError.message || 'Не удалось добавить позицию'
  } finally {
    isAdding.value = false
  }
}

async function toggleBought(item) {
  error.value = ''
  try {
    const updated = await api.patch(`/shopping-items/${item.id}`, {
      is_bought: !item.is_bought
    })
    items.value = items.value.map((current) => (current.id === item.id ? updated : current))
  } catch (requestError) {
    error.value = requestError.message || 'Не удалось обновить позицию'
  }
}

async function removeItem(item) {
  error.value = ''
  try {
    await api.delete(`/shopping-items/${item.id}`)
    items.value = items.value.filter((current) => current.id !== item.id)
  } catch (requestError) {
    error.value = requestError.message || 'Не удалось удалить позицию'
  }
}

onMounted(loadItems)
</script>

<template>
  <section class="page-section">
    <div class="section-header">
      <div>
        <p class="eyebrow">Покупки</p>
        <h1>Список покупок</h1>
      </div>
    </div>

    <form class="shopping-add" @submit.prevent="addItem">
      <input
        v-model.trim="newItem.name"
        placeholder="Что купить, например «Пластырь»"
        aria-label="Название позиции"
        maxlength="180"
        required
      />
      <input
        v-model.trim="newItem.note"
        placeholder="Заметка (дозировка, количество)"
        aria-label="Заметка"
      />
      <button class="primary-button inline-button" type="submit" :disabled="isAdding">
        {{ isAdding ? 'Добавляем...' : 'Добавить' }}
      </button>
    </form>

    <p v-if="error" class="form-error">{{ error }}</p>
    <p v-if="isLoading" class="muted">Загружаем список...</p>

    <template v-else-if="items.length">
      <ul class="shopping-list">
        <li v-for="item in pendingItems" :key="item.id" class="shopping-item">
          <label class="shopping-check">
            <input
              type="checkbox"
              :checked="item.is_bought"
              :aria-label="`Отметить «${item.name}» купленным`"
              @change="toggleBought(item)"
            />
            <span class="shopping-text">
              <span class="shopping-name">{{ item.name }}</span>
              <span v-if="item.note" class="shopping-note">{{ item.note }}</span>
              <span class="shopping-meta">добавлено {{ formatDateTime(item.created_at) }}</span>
            </span>
          </label>
          <button class="text-button danger-button" type="button" @click="removeItem(item)">
            Удалить
          </button>
        </li>
      </ul>

      <details v-if="boughtItems.length" class="bought-block" open>
        <summary>Куплено ({{ boughtItems.length }})</summary>
        <ul class="shopping-list">
          <li v-for="item in boughtItems" :key="item.id" class="shopping-item shopping-item-bought">
            <label class="shopping-check">
              <input
                type="checkbox"
                :checked="item.is_bought"
                :aria-label="`Вернуть «${item.name}» в список`"
                @change="toggleBought(item)"
              />
              <span class="shopping-text">
                <span class="shopping-name">{{ item.name }}</span>
                <span v-if="item.note" class="shopping-note">{{ item.note }}</span>
              </span>
            </label>
            <button class="text-button danger-button" type="button" @click="removeItem(item)">
              Удалить
            </button>
          </li>
        </ul>
      </details>
    </template>

    <div v-else class="empty-state">
      <h2>Покупок пока нет</h2>
      <p>Добавьте позицию выше или нажмите «В покупки» на карточке лекарства в аптечке.</p>
    </div>
  </section>
</template>
