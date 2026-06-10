export const FORM_OPTIONS = [
  { value: 'tablets', label: 'Таблетки' },
  { value: 'syrup', label: 'Сироп' },
  { value: 'ointment', label: 'Мазь' },
  { value: 'drops', label: 'Капли' },
  { value: 'capsules', label: 'Капсулы' },
  { value: 'spray', label: 'Спрей' },
  { value: 'other', label: 'Другое' }
]

export const UNIT_OPTIONS = [
  { value: 'tablet', label: 'таблетки' },
  { value: 'ml', label: 'мл' },
  { value: 'g', label: 'г' },
  { value: 'piece', label: 'шт' },
  { value: 'drop', label: 'капли' },
  { value: 'other', label: 'другое' }
]

export const STORAGE_OPTIONS = [
  { value: 'kit', label: 'Аптечка' },
  { value: 'fridge', label: 'Холодильник' },
  { value: 'kids_kit', label: 'Детская аптечка' }
]

export const STATUS_OPTIONS = [
  { value: 'ok', label: 'Годно' },
  { value: 'expiring_warning', label: 'Истекает в 90 дней' },
  { value: 'expiring_soon', label: 'Скоро истекает' },
  { value: 'expired', label: 'Просрочено' }
]

const FORM_LABELS = Object.fromEntries(FORM_OPTIONS.map((item) => [item.value, item.label]))
const UNIT_LABELS = Object.fromEntries(UNIT_OPTIONS.map((item) => [item.value, item.label]))
const STORAGE_LABELS = Object.fromEntries(STORAGE_OPTIONS.map((item) => [item.value, item.label]))
const STATUS_LABELS = Object.fromEntries(STATUS_OPTIONS.map((item) => [item.value, item.label]))

export const formLabel = (value) => FORM_LABELS[value] || value || '—'
export const unitLabel = (value) => UNIT_LABELS[value] || value || ''
export const storageLabel = (value) => STORAGE_LABELS[value] || value || '—'
export const statusLabel = (value) => STATUS_LABELS[value] || value || '—'

// Парсер справочника возвращает лекарственную форму свободным текстом
// («капсулы 300 мг», «гель для наружного применения») — сводим её к choices модели.
const FORM_TEXT_PATTERNS = [
  { pattern: /таблет|tablet/i, value: 'tablets' },
  { pattern: /капсул|capsule/i, value: 'capsules' },
  { pattern: /сироп|syrup/i, value: 'syrup' },
  { pattern: /мазь|гель|крем|ointment|gel|cream/i, value: 'ointment' },
  { pattern: /капл|drop/i, value: 'drops' },
  { pattern: /спрей|аэрозол|spray/i, value: 'spray' }
]

export function matchFormChoice(text) {
  const found = FORM_TEXT_PATTERNS.find(({ pattern }) => pattern.test(text || ''))
  return found ? found.value : 'other'
}

// Названия секций reference_data для «инструкции-заметки».
export const REFERENCE_SECTION_LABELS = {
  active_substance: 'Действующее вещество',
  pharmacological_group: 'Фармакологическая группа',
  dosage_form: 'Лекарственная форма',
  composition: 'Состав',
  indications: 'Показания',
  contraindications: 'Противопоказания',
  pregnancy_lactation: 'Беременность и лактация',
  administration: 'Способ применения и дозы',
  side_effects: 'Побочные действия',
  interactions: 'Взаимодействие',
  overdose: 'Передозировка',
  special_instructions: 'Особые указания',
  release_form: 'Форма выпуска',
  pharmacy_terms: 'Условия отпуска из аптек',
  storage_conditions: 'Условия хранения',
  shelf_life: 'Срок годности',
  manufacturer: 'Производитель'
}
