<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../api/client'
import StatusBadge from '../components/StatusBadge.vue'
import {
  STATUS_OPTIONS,
  STORAGE_OPTIONS,
  formLabel,
  storageLabel,
  unitLabel
} from '../constants/medicine'
import { formatExpiryMonth, formatQuantity } from '../utils/expiry'

const medicines = ref([])
const isLoading = ref(true)
const error = ref('')
const notice = ref('')

const filters = reactive({
  search: '',
  status: '',
  storage: '',
  lowStock: false
})

let searchDebounce = null

const hasFilters = computed(() =>
  Boolean(filters.search || filters.status || filters.storage || filters.lowStock)
)

async function loadMedicines() {
  isLoading.value = true
  error.value = ''

  const params = new URLSearchParams()
  if (filters.search) params.set('search', filters.search)
  if (filters.status) params.set('status', filters.status)
  if (filters.storage) params.set('storage', filters.storage)
  if (filters.lowStock) params.set('low_stock', 'true')
  const query = params.toString()

  try {
    medicines.value = await api.get(`/medicines${query ? `?${query}` : ''}`)
  } catch (requestError) {
    error.value = requestError.message || 'Не удалось загрузить аптечку'
  } finally {
    isLoading.value = false
  }
}

watch(
  () => filters.search,
  () => {
    clearTimeout(searchDebounce)
    searchDebounce = setTimeout(loadMedicines, 350)
  }
)

onBeforeUnmount(() => clearTimeout(searchDebounce))

function toggleFilter(name, value) {
  filters[name] = filters[name] === value ? '' : value
  loadMedicines()
}

function toggleLowStockFilter() {
  filters.lowStock = !filters.lowStock
  loadMedicines()
}

function resetFilters() {
  filters.search = ''
  filters.status = ''
  filters.storage = ''
  filters.lowStock = false
  loadMedicines()
}

async function recordIntake(medicine, amount) {
  notice.value = ''
  error.value = ''

  try {
    const updated = await api.post(`/medicines/${medicine.id}/intake`, { amount })
    const index = medicines.value.findIndex((item) => item.id === medicine.id)
    if (index !== -1) {
      // При активном фильтре «Заканчиваются» позиция могла перестать ему соответствовать,
      // но не убираем её сразу — пользователь видит результат списания.
      medicines.value[index] = updated
    }
    notice.value = `«${medicine.trade_name}»: списано ${formatQuantity(amount)} ${unitLabel(medicine.unit)}, осталось ${formatQuantity(updated.quantity)}`
  } catch (requestError) {
    error.value = requestError.message || 'Не удалось отметить приём'
  }
}

function recordCustomIntake(medicine) {
  const raw = window.prompt(
    `Сколько ${unitLabel(medicine.unit)} списать из «${medicine.trade_name}»?`,
    '1'
  )
  if (raw === null) {
    return
  }

  const amount = Number(String(raw).trim().replace(',', '.'))
  if (!Number.isFinite(amount) || amount <= 0) {
    error.value = 'Введите число больше нуля.'
    return
  }
  recordIntake(medicine, amount)
}

async function addToShopping(medicine) {
  notice.value = ''
  error.value = ''

  try {
    await api.post('/shopping-items', {
      medicine: medicine.id,
      name: medicine.trade_name,
      note: [medicine.dosage, formLabel(medicine.form)].filter(Boolean).join(', ')
    })
    notice.value = `«${medicine.trade_name}» добавлено в список покупок`
  } catch (requestError) {
    error.value = requestError.message || 'Не удалось добавить в покупки'
  }
}

async function removeMedicine(medicine) {
  if (!window.confirm(`Удалить «${medicine.trade_name}» из аптечки?`)) {
    return
  }

  error.value = ''
  try {
    await api.delete(`/medicines/${medicine.id}`)
    medicines.value = medicines.value.filter((item) => item.id !== medicine.id)
  } catch (requestError) {
    error.value = requestError.message || 'Не удалось удалить лекарство'
  }
}

onMounted(loadMedicines)
</script>

<template>
  <section class="page-section">
    <div class="section-header">
      <div>
        <p class="eyebrow">Аптечка</p>
        <h1>Лекарства</h1>
      </div>
      <RouterLink class="primary-button inline-button" to="/medicines/new">
        + Добавить
      </RouterLink>
    </div>

    <div class="filter-bar">
      <input
        v-model.trim="filters.search"
        class="search-input"
        type="search"
        placeholder="Поиск по названию или действующему веществу"
        aria-label="Поиск лекарства"
      />

      <div class="chip-row" role="group" aria-label="Фильтр по статусу">
        <button
          v-for="option in STATUS_OPTIONS"
          :key="option.value"
          type="button"
          class="chip"
          :class="{ 'chip-active': filters.status === option.value }"
          :data-status="option.value"
          @click="toggleFilter('status', option.value)"
        >
          {{ option.label }}
        </button>
      </div>

      <div class="chip-row" role="group" aria-label="Фильтр по месту хранения">
        <button
          v-for="option in STORAGE_OPTIONS"
          :key="option.value"
          type="button"
          class="chip"
          :class="{ 'chip-active': filters.storage === option.value }"
          @click="toggleFilter('storage', option.value)"
        >
          {{ option.label }}
        </button>
        <button
          type="button"
          class="chip"
          :class="{ 'chip-active chip-low-stock': filters.lowStock }"
          @click="toggleLowStockFilter"
        >
          Заканчиваются
        </button>
        <button v-if="hasFilters" type="button" class="chip chip-reset" @click="resetFilters">
          Сбросить
        </button>
      </div>
    </div>

    <p v-if="notice" class="form-notice" role="status">{{ notice }}</p>
    <p v-if="error" class="form-error">{{ error }}</p>

    <p v-if="isLoading" class="muted">Загружаем аптечку...</p>

    <div v-else-if="medicines.length" class="medicine-grid">
      <article v-for="medicine in medicines" :key="medicine.id" class="medicine-card">
        <RouterLink
          class="medicine-photo"
          :to="`/medicines/${medicine.id}/edit`"
          :aria-label="`Открыть ${medicine.trade_name}`"
        >
          <img v-if="medicine.photo" :src="medicine.photo" :alt="medicine.trade_name" loading="lazy" />
          <span v-else class="medicine-photo-placeholder" aria-hidden="true">💊</span>
          <StatusBadge class="medicine-status" :status="medicine.status" />
        </RouterLink>

        <div class="medicine-body">
          <h2 class="medicine-name">
            <RouterLink :to="`/medicines/${medicine.id}/edit`">{{ medicine.trade_name }}</RouterLink>
          </h2>
          <p v-if="medicine.active_ingredient" class="medicine-ingredient">
            {{ medicine.active_ingredient }}
          </p>

          <dl class="medicine-facts">
            <div>
              <dt>Форма</dt>
              <dd>{{ formLabel(medicine.form) }}<template v-if="medicine.dosage">, {{ medicine.dosage }}</template></dd>
            </div>
            <div>
              <dt>Остаток</dt>
              <dd class="quantity-row">
                <span :class="{ 'low-stock-text': medicine.is_low_stock }">
                  {{ formatQuantity(medicine.quantity) }} {{ unitLabel(medicine.unit) }}
                </span>
                <button
                  class="intake-button"
                  type="button"
                  :disabled="Number(medicine.quantity) <= 0"
                  :aria-label="`Отметить приём: ${medicine.trade_name}, минус 1`"
                  title="Отметить приём одной единицы"
                  @click="recordIntake(medicine, 1)"
                >
                  −1
                </button>
                <button
                  class="intake-button"
                  type="button"
                  :disabled="Number(medicine.quantity) <= 0"
                  :aria-label="`Списать произвольное количество: ${medicine.trade_name}`"
                  title="Списать произвольное количество"
                  @click="recordCustomIntake(medicine)"
                >
                  −…
                </button>
                <span v-if="medicine.is_low_stock" class="low-stock-badge">
                  Заканчивается — пора покупать
                </span>
              </dd>
            </div>
            <div>
              <dt>Годен до</dt>
              <dd>{{ formatExpiryMonth(medicine.expiry_date) }}</dd>
            </div>
            <div>
              <dt>Хранение</dt>
              <dd>{{ storageLabel(medicine.storage) }}</dd>
            </div>
          </dl>
        </div>

        <div class="medicine-actions">
          <RouterLink class="text-button" :to="`/medicines/${medicine.id}/edit`">Изменить</RouterLink>
          <button class="text-button" type="button" @click="addToShopping(medicine)">В покупки</button>
          <button class="text-button danger-button" type="button" @click="removeMedicine(medicine)">
            Удалить
          </button>
        </div>
      </article>
    </div>

    <div v-else class="empty-state">
      <h2>{{ hasFilters ? 'Ничего не найдено' : 'Аптечка пока пуста' }}</h2>
      <p v-if="hasFilters">Попробуйте изменить запрос или сбросить фильтры.</p>
      <p v-else>
        Добавьте первое лекарство — вручную или автозаполнением по ссылке на справочник.
      </p>
    </div>
  </section>
</template>
