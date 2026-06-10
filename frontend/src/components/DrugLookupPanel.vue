<script setup>
import { computed, ref } from 'vue'
import { api } from '../api/client'

const emit = defineEmits(['filled'])

const url = ref('')
const tradeName = ref('')
const variants = ref([])
const selectedIndex = ref(null)
const error = ref('')
const isLoadingForms = ref(false)
const isParsing = ref(false)

const isBusy = computed(() => isLoadingForms.value || isParsing.value)
const showVariantPicker = computed(() => variants.value.length > 0)

function variantTitle(variant) {
  return [variant.form, variant.dosage].filter(Boolean).join(' · ') || 'Вариант без описания'
}

function resetResults() {
  tradeName.value = ''
  variants.value = []
  selectedIndex.value = null
}

async function findForms() {
  error.value = ''
  resetResults()
  isLoadingForms.value = true

  try {
    const response = await api.post('/drug-lookup/forms', { url: url.value })
    if (!response.ok) {
      throw new Error(response.error)
    }

    tradeName.value = response.trade_name

    if (response.single_variant) {
      // Страница без таблицы выбора форм — сразу разбираем единственный вариант.
      await parseVariant(response.variants[0] || { form: '', dosage: '' })
      return
    }

    variants.value = response.variants
    selectedIndex.value = response.variants.length === 1 ? 0 : null
  } catch (requestError) {
    error.value = requestError.message || 'Не удалось разобрать ссылку'
  } finally {
    isLoadingForms.value = false
  }
}

async function parseVariant(variant) {
  error.value = ''
  isParsing.value = true

  try {
    const response = await api.post('/drug-lookup/parse', {
      url: url.value,
      form: variant.form || '',
      dosage: variant.dosage || ''
    })
    if (!response.ok) {
      throw new Error(response.error)
    }

    emit('filled', response)
    resetResults()
  } catch (requestError) {
    error.value = requestError.message || 'Не удалось разобрать выбранный вариант'
  } finally {
    isParsing.value = false
  }
}

function fillSelected() {
  if (selectedIndex.value === null) {
    return
  }

  parseVariant(variants.value[selectedIndex.value])
}
</script>

<template>
  <section class="lookup-panel">
    <header>
      <h2>Автозаполнение по ссылке</h2>
      <p class="muted">
        Вставьте ссылку на страницу препарата в справочнике — мы найдём формы выпуска и
        заполним поля. Любое значение можно поправить перед сохранением.
      </p>
    </header>

    <div class="lookup-input-row">
      <input
        v-model.trim="url"
        type="url"
        inputmode="url"
        placeholder="https://..."
        aria-label="Ссылка на справочник"
        :disabled="isBusy"
        @keydown.enter.prevent="url && findForms()"
      />
      <button class="primary-button inline-button" type="button" :disabled="!url || isBusy" @click="findForms">
        {{ isLoadingForms ? 'Ищем формы...' : 'Найти формы' }}
      </button>
    </div>

    <p v-if="isBusy" class="muted lookup-progress" role="status">
      <span class="spinner" aria-hidden="true"></span>
      {{ isParsing ? 'Разбираем описание препарата — это занимает несколько секунд...' : 'Открываем страницу и ищем варианты...' }}
    </p>

    <p v-if="error" class="form-error">
      {{ error }} Можно заполнить поля вручную ниже.
    </p>

    <div v-if="showVariantPicker && !isParsing" class="lookup-variants">
      <h3>{{ tradeName || 'Найденные варианты' }}: выберите форму и дозировку</h3>
      <div class="variant-list" role="radiogroup" aria-label="Варианты лекарственной формы">
        <label
          v-for="(variant, index) in variants"
          :key="`${variant.form}-${variant.dosage}`"
          class="variant-option"
          :class="{ 'variant-selected': selectedIndex === index }"
        >
          <input v-model="selectedIndex" type="radio" name="drug-variant" :value="index" />
          <span class="variant-form">{{ variant.form || 'Форма не указана' }}</span>
          <span class="variant-dosage">{{ variant.dosage || '—' }}</span>
        </label>
      </div>
      <button
        class="primary-button inline-button"
        type="button"
        :disabled="selectedIndex === null || isBusy"
        @click="fillSelected"
      >
        Заполнить форму
      </button>
    </div>
  </section>
</template>
