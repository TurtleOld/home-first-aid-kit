<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'
import DrugLookupPanel from '../components/DrugLookupPanel.vue'
import MediaImage from '../components/MediaImage.vue'
import ReferenceDataNote from '../components/ReferenceDataNote.vue'
import {
  FORM_OPTIONS,
  STORAGE_OPTIONS,
  UNIT_OPTIONS,
  matchFormChoice
} from '../constants/medicine'
import { MONTH_OPTIONS, isoDateToMonthYear, monthYearToIsoDate } from '../utils/expiry'
import { compressImageFile } from '../utils/image'

const route = useRoute()
const router = useRouter()

const medicineId = computed(() => route.params.id || null)
const isEdit = computed(() => Boolean(medicineId.value))

const form = reactive({
  trade_name: '',
  active_ingredient: '',
  form: 'tablets',
  dosage: '',
  quantity: '',
  unit: 'piece',
  low_stock_threshold: '',
  storage: 'kit',
  notes: '',
  instruction_url: '',
  instruction_note: ''
})
const expiry = reactive({ month: null, year: null })
const sourceUrl = ref('')
const referenceData = ref(null)

const photoFile = ref(null)
const photoPreview = ref('')
const existingPhotoUrl = ref('')
const removePhoto = ref(false)

const instructionFile = ref(null)
const existingInstructionUrl = ref('')
const removeInstructionFile = ref(false)

const INSTRUCTION_TABS = [
  { value: 'file', label: 'Файл' },
  { value: 'url', label: 'Ссылка' },
  { value: 'note', label: 'Заметка' }
]
const instructionTab = ref('url')

const isLoading = ref(false)
const isSaving = ref(false)
const error = ref('')
const notice = ref('')

const yearNow = new Date().getFullYear()
const YEAR_OPTIONS = Array.from({ length: 26 }, (_, index) => yearNow - 12 + index)

onMounted(async () => {
  if (!isEdit.value) {
    return
  }

  isLoading.value = true
  try {
    const medicine = await api.get(`/medicines/${medicineId.value}`)
    Object.keys(form).forEach((key) => {
      form[key] = medicine[key] ?? ''
    })
    form.quantity = medicine.quantity ?? ''
    Object.assign(expiry, isoDateToMonthYear(medicine.expiry_date))
    sourceUrl.value = medicine.source_url || ''
    referenceData.value = medicine.reference_data
    existingPhotoUrl.value = medicine.photo || ''
    existingInstructionUrl.value = medicine.instruction_file || ''
    if (medicine.instruction_note) {
      instructionTab.value = 'note'
    } else if (medicine.instruction_file) {
      instructionTab.value = 'file'
    }
  } catch (requestError) {
    error.value = requestError.message || 'Не удалось загрузить лекарство'
  } finally {
    isLoading.value = false
  }
})

async function onPhotoChange(event) {
  const file = event.target.files?.[0] || null
  removePhoto.value = false

  if (photoPreview.value) {
    URL.revokeObjectURL(photoPreview.value)
    photoPreview.value = ''
  }

  if (!file) {
    photoFile.value = null
    return
  }

  photoFile.value = await compressImageFile(file)
  photoPreview.value = URL.createObjectURL(photoFile.value)
}

function clearPhoto() {
  photoFile.value = null
  if (photoPreview.value) {
    URL.revokeObjectURL(photoPreview.value)
    photoPreview.value = ''
  }
  if (existingPhotoUrl.value) {
    removePhoto.value = true
    existingPhotoUrl.value = ''
  }
}

onBeforeUnmount(() => {
  if (photoPreview.value) {
    URL.revokeObjectURL(photoPreview.value)
  }
})

function onInstructionFileChange(event) {
  instructionFile.value = event.target.files?.[0] || null
  removeInstructionFile.value = false
}

async function openInstructionFile() {
  if (!existingInstructionUrl.value) {
    return
  }

  try {
    const blob = await api.getBlob(existingInstructionUrl.value)
    const objectUrl = URL.createObjectURL(blob)
    window.open(objectUrl, '_blank', 'noopener')
    setTimeout(() => URL.revokeObjectURL(objectUrl), 60000)
  } catch (requestError) {
    error.value = requestError.message || 'Не удалось открыть файл'
  }
}

function clearInstructionFile() {
  instructionFile.value = null
  if (existingInstructionUrl.value) {
    removeInstructionFile.value = true
    existingInstructionUrl.value = ''
  }
}

function appendNoteLine(line) {
  if (!line || form.notes.includes(line)) {
    return
  }
  form.notes = form.notes ? `${form.notes}\n${line}` : line
}

function onLookupFilled(result) {
  const fields = result.fields || {}

  if (fields.trade_name) form.trade_name = fields.trade_name
  if (fields.active_ingredient) form.active_ingredient = fields.active_ingredient
  if (fields.dosage) form.dosage = fields.dosage
  if (fields.form) form.form = matchFormChoice(fields.form)

  // Условия хранения и срок из справочника — текст, а не дата: кладём в примечания,
  // срок годности конкретной упаковки пользователь вводит сам.
  appendNoteLine(fields.storage_conditions)
  appendNoteLine(fields.shelf_life)

  sourceUrl.value = result.source_url || sourceUrl.value
  referenceData.value = result.reference_data || null

  const matches = result.selected_matches_description
  notice.value =
    matches && !matches.overall
      ? 'Поля заполнены, но описание могло не совпасть с выбранным вариантом — проверьте значения.'
      : 'Поля заполнены из справочника. Проверьте их и укажите количество и срок годности.'
  error.value = ''
}

function clearReferenceData() {
  referenceData.value = null
  sourceUrl.value = ''
}

function buildPayload() {
  return {
    ...form,
    quantity: form.quantity === '' ? '0' : String(form.quantity),
    low_stock_threshold:
      form.low_stock_threshold === '' || form.low_stock_threshold === null
        ? null
        : String(form.low_stock_threshold),
    expiry_date: monthYearToIsoDate(expiry.month, expiry.year),
    source_url: sourceUrl.value,
    reference_data: referenceData.value
  }
}

function buildFormData(payload) {
  const data = new FormData()
  Object.entries(payload).forEach(([key, value]) => {
    if (key === 'reference_data') {
      data.append(key, value ? JSON.stringify(value) : '')
      return
    }
    data.append(key, value ?? '')
  })
  if (photoFile.value) {
    data.append('photo', photoFile.value)
  }
  if (instructionFile.value) {
    data.append('instruction_file', instructionFile.value)
  }
  return data
}

async function save() {
  error.value = ''

  if (!expiry.month || !expiry.year) {
    error.value = 'Укажите срок годности — месяц и год.'
    return
  }

  isSaving.value = true
  try {
    const payload = buildPayload()
    const hasFiles = Boolean(photoFile.value || instructionFile.value)
    const clears = {}
    if (removePhoto.value && !photoFile.value) clears.photo = null
    if (removeInstructionFile.value && !instructionFile.value) clears.instruction_file = null

    let saved
    if (hasFiles) {
      const data = buildFormData(payload)
      saved = isEdit.value
        ? await api.patchForm(`/medicines/${medicineId.value}`, data)
        : await api.postForm('/medicines', data)
    } else {
      const body = { ...payload, ...clears }
      saved = isEdit.value
        ? await api.patch(`/medicines/${medicineId.value}`, body)
        : await api.post('/medicines', body)
    }

    // Файл нельзя удалить через multipart — снимаем отдельным PATCH'ем.
    if (hasFiles && Object.keys(clears).length) {
      await api.patch(`/medicines/${saved.id}`, clears)
    }

    router.push('/medicines')
  } catch (requestError) {
    error.value = requestError.message || 'Не удалось сохранить лекарство'
  } finally {
    isSaving.value = false
  }
}

async function removeMedicine() {
  if (!window.confirm(`Удалить «${form.trade_name}» из аптечки?`)) {
    return
  }

  error.value = ''
  try {
    await api.delete(`/medicines/${medicineId.value}`)
    router.push('/medicines')
  } catch (requestError) {
    error.value = requestError.message || 'Не удалось удалить лекарство'
  }
}
</script>

<template>
  <section class="page-section">
    <div class="section-header">
      <div>
        <p class="eyebrow">Аптечка</p>
        <h1>{{ isEdit ? 'Лекарство' : 'Новое лекарство' }}</h1>
      </div>
      <button
        v-if="isEdit"
        class="text-button danger-button"
        type="button"
        @click="removeMedicine"
      >
        Удалить
      </button>
    </div>

    <p v-if="isLoading" class="muted">Загружаем...</p>

    <template v-else>
      <DrugLookupPanel v-if="!isEdit" @filled="onLookupFilled" />

      <form class="medicine-form" @submit.prevent="save">
        <p v-if="notice" class="form-notice" role="status">{{ notice }}</p>

        <fieldset>
          <legend>Описание</legend>
          <div class="form-grid">
            <label>
              Торговое название *
              <input v-model.trim="form.trade_name" required maxlength="180" placeholder="Нурофен" />
            </label>
            <label>
              Действующее вещество
              <input v-model.trim="form.active_ingredient" maxlength="180" placeholder="ибупрофен" />
            </label>
            <label>
              Лекарственная форма
              <select v-model="form.form">
                <option v-for="option in FORM_OPTIONS" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </label>
            <label>
              Дозировка
              <input v-model.trim="form.dosage" maxlength="120" placeholder="200 мг" />
            </label>
          </div>
        </fieldset>

        <fieldset>
          <legend>Наличие и срок</legend>
          <div class="form-grid form-grid-3">
            <label>
              Количество *
              <input v-model="form.quantity" type="number" min="0" step="any" required />
            </label>
            <label>
              Единица
              <select v-model="form.unit">
                <option v-for="option in UNIT_OPTIONS" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </label>
            <label>
              Место хранения
              <select v-model="form.storage">
                <option v-for="option in STORAGE_OPTIONS" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </label>
          </div>

          <label>
            Порог «заканчивается»
            <input
              v-model="form.low_stock_threshold"
              type="number"
              min="0"
              step="any"
              placeholder="например, 5"
            />
            <span class="field-caption">
              Когда остаток опустится до этого значения, лекарство будет помечено как
              заканчивающееся. Оставьте пустым, чтобы не отслеживать.
            </span>
          </label>

          <div class="expiry-row">
            <span class="field-caption">Годен до (месяц и год) *</span>
            <div class="expiry-inputs">
              <select v-model.number="expiry.month" aria-label="Месяц срока годности" required>
                <option :value="null" disabled>Месяц</option>
                <option v-for="month in MONTH_OPTIONS" :key="month.value" :value="month.value">
                  {{ month.label }}
                </option>
              </select>
              <select v-model.number="expiry.year" aria-label="Год срока годности" required>
                <option :value="null" disabled>Год</option>
                <option v-for="year in YEAR_OPTIONS" :key="year" :value="year">{{ year }}</option>
              </select>
            </div>
          </div>
        </fieldset>

        <fieldset>
          <legend>Фото упаковки</legend>
          <div class="photo-field">
            <img v-if="photoPreview" class="photo-preview" :src="photoPreview" alt="Фото лекарства" />
            <MediaImage
              v-else-if="existingPhotoUrl"
              class="photo-preview"
              :src="existingPhotoUrl"
              alt="Фото лекарства"
            />
            <div class="photo-controls">
              <input type="file" accept="image/*" @change="onPhotoChange" />
              <button
                v-if="photoPreview || existingPhotoUrl"
                class="text-button"
                type="button"
                @click="clearPhoto"
              >
                Убрать фото
              </button>
            </div>
          </div>
        </fieldset>

        <fieldset>
          <legend>Инструкция</legend>
          <div class="segmented" role="tablist" aria-label="Способ хранения инструкции">
            <button
              v-for="tab in INSTRUCTION_TABS"
              :key="tab.value"
              type="button"
              role="tab"
              :aria-selected="instructionTab === tab.value"
              class="segmented-option"
              :class="{ 'segmented-active': instructionTab === tab.value }"
              @click="instructionTab = tab.value"
            >
              {{ tab.label }}
            </button>
          </div>

          <div v-if="instructionTab === 'file'" class="instruction-pane">
            <p v-if="existingInstructionUrl" class="muted">
              Загружен файл:
              <button class="text-button" type="button" @click="openInstructionFile">открыть</button>
              <button class="text-button" type="button" @click="clearInstructionFile">Убрать</button>
            </p>
            <input type="file" accept=".pdf,.doc,.docx,.txt,image/*" @change="onInstructionFileChange" />
          </div>

          <label v-else-if="instructionTab === 'url'" class="instruction-pane">
            Ссылка на инструкцию
            <input v-model.trim="form.instruction_url" type="url" placeholder="https://..." />
          </label>

          <label v-else class="instruction-pane">
            Текст заметки
            <textarea v-model="form.instruction_note" rows="4" placeholder="Принимать после еды..."></textarea>
          </label>

          <div v-if="referenceData" class="reference-block">
            <ReferenceDataNote :reference-data="referenceData" />
            <p class="muted reference-source">
              Источник: <a :href="sourceUrl" target="_blank" rel="noopener">{{ sourceUrl }}</a>
              <button class="text-button" type="button" @click="clearReferenceData">Убрать</button>
            </p>
          </div>
        </fieldset>

        <fieldset>
          <legend>Примечания</legend>
          <label>
            Заметки (хранение, для кого и т.п.)
            <textarea v-model="form.notes" rows="3" placeholder="Хранить при температуре не выше 25 °C"></textarea>
          </label>
        </fieldset>

        <p v-if="error" class="form-error">{{ error }}</p>

        <div class="form-actions">
          <button class="primary-button inline-button" type="submit" :disabled="isSaving">
            {{ isSaving ? 'Сохраняем...' : isEdit ? 'Сохранить изменения' : 'Добавить в аптечку' }}
          </button>
          <button class="text-button" type="button" @click="router.push('/medicines')">Отмена</button>
        </div>
      </form>
    </template>
  </section>
</template>
