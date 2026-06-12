<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api/client'
import Skeleton from '../components/Skeleton.vue'
import { formLabel, statusLabel, storageLabel, unitLabel } from '../constants/medicine'
import { formatDateTime, formatExpiryMonth } from '../utils/expiry'

const entries = ref([])
const count = ref(0)
const page = ref(1)
const hasNext = ref(false)
const hasPrev = ref(false)
const isLoading = ref(true)
const error = ref('')

const PAGE_SIZE = 20
const totalPages = computed(() => Math.max(1, Math.ceil(count.value / PAGE_SIZE)))

const ACTION_LABELS = {
  create: 'добавил(а)',
  update: 'изменил(а)',
  delete: 'удалил(а)',
  intake: 'отметил(а) приём:'
}

const ENTITY_LABELS = {
  medicine: 'лекарство',
  shoppingitem: 'позицию покупок'
}

const FIELD_LABELS = {
  trade_name: 'Название',
  active_ingredient: 'Действующее вещество',
  form: 'Форма',
  dosage: 'Дозировка',
  quantity: 'Количество',
  unit: 'Единица',
  low_stock_threshold: 'Порог остатка',
  expiry_date: 'Срок годности',
  storage: 'Хранение',
  notes: 'Заметки',
  instruction_url: 'Ссылка на инструкцию',
  instruction_note: 'Заметка-инструкция',
  source_url: 'Источник',
  reference_data: 'Инструкция из справочника',
  medicine: 'Лекарство',
  name: 'Название',
  note: 'Заметка',
  is_bought: 'Куплено'
}

function formatValue(field, value) {
  if (value === null || value === undefined || value === '') {
    return '—'
  }

  switch (field) {
    case 'form':
      return formLabel(value)
    case 'unit':
      return unitLabel(value)
    case 'storage':
      return storageLabel(value)
    case 'status':
      return statusLabel(value)
    case 'expiry_date':
      return formatExpiryMonth(value)
    case 'is_bought':
      return value ? 'да' : 'нет'
    case 'reference_data':
      return typeof value === 'object' ? 'заполнена' : String(value)
    default:
      if (typeof value === 'object') {
        return JSON.stringify(value)
      }
      return String(value)
  }
}

function fieldLabel(field) {
  return FIELD_LABELS[field] || field
}

function actionText(entry) {
  const action = ACTION_LABELS[entry.action] || entry.action
  const entity = ENTITY_LABELS[entry.entity_type] || entry.entity_type
  return `${action} ${entity}`
}

function actorName(entry) {
  return entry.actor?.username || 'Кто-то'
}

// Diff показываем для update и intake; create/delete сворачиваем в одну строку.
function entryDiff(entry) {
  if (entry.action !== 'update' && entry.action !== 'intake') {
    return []
  }

  return Object.entries(entry.changes || {})
    .filter(([, change]) => change && typeof change === 'object' && ('old' in change || 'new' in change))
    .map(([field, change]) => ({
      field: fieldLabel(field),
      old: formatValue(field, change.old),
      new: formatValue(field, change.new)
    }))
}

async function loadPage(target = 1) {
  isLoading.value = true
  error.value = ''

  try {
    const response = await api.get(`/changelog?page=${target}`)
    entries.value = response.results
    count.value = response.count
    hasNext.value = Boolean(response.next)
    hasPrev.value = Boolean(response.previous)
    page.value = target
  } catch (requestError) {
    error.value = requestError.message || 'Не удалось загрузить журнал'
  } finally {
    isLoading.value = false
  }
}

onMounted(() => loadPage(1))
</script>

<template>
  <section class="page-section">
    <div class="section-header">
      <div>
        <p class="eyebrow">Журнал</p>
        <h1>История изменений</h1>
      </div>
      <p v-if="count" class="muted">Всего записей: {{ count }}</p>
    </div>

    <p v-if="error" class="form-error">{{ error }}</p>

    <ul v-if="isLoading" class="changelog-list" aria-hidden="true">
      <li v-for="n in 5" :key="n" class="skeleton-row">
        <div class="skeleton-row-text">
          <Skeleton width="60%" />
          <Skeleton width="35%" />
        </div>
      </li>
    </ul>

    <ol v-else-if="entries.length" class="changelog-list">
      <li v-for="entry in entries" :key="entry.id" class="changelog-entry" :data-action="entry.action">
        <span class="changelog-marker" aria-hidden="true"></span>
        <div class="changelog-body">
          <p class="changelog-title">
            <strong>{{ actorName(entry) }}</strong>
            {{ actionText(entry) }}
            <strong>«{{ entry.entity_repr }}»</strong>
          </p>

          <ul v-if="entryDiff(entry).length" class="changelog-diff">
            <li v-for="change in entryDiff(entry)" :key="change.field">
              {{ change.field }}: <s>{{ change.old }}</s> → <strong>{{ change.new }}</strong>
            </li>
          </ul>

          <time class="changelog-time" :datetime="entry.created_at">
            {{ formatDateTime(entry.created_at) }}
          </time>
        </div>
      </li>
    </ol>

    <div v-else class="empty-state">
      <h2>Событий пока нет</h2>
      <p>После добавления лекарств и покупок здесь будет общая лента изменений семьи.</p>
    </div>

    <nav v-if="hasNext || hasPrev" class="pagination" aria-label="Страницы журнала">
      <button class="text-button" type="button" :disabled="!hasPrev || isLoading" @click="loadPage(page - 1)">
        ← Новее
      </button>
      <span class="muted">Страница {{ page }} из {{ totalPages }}</span>
      <button class="text-button" type="button" :disabled="!hasNext || isLoading" @click="loadPage(page + 1)">
        Старее →
      </button>
    </nav>
  </section>
</template>
