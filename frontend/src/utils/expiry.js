const MONTH_LABELS = [
  'Январь',
  'Февраль',
  'Март',
  'Апрель',
  'Май',
  'Июнь',
  'Июль',
  'Август',
  'Сентябрь',
  'Октябрь',
  'Ноябрь',
  'Декабрь'
]

export const MONTH_OPTIONS = MONTH_LABELS.map((label, index) => ({
  value: index + 1,
  label
}))

// Срок годности вводится как месяц+год, бэкенд хранит дату —
// берём последний день месяца (лекарство годно весь указанный месяц).
export function monthYearToIsoDate(month, year) {
  if (!month || !year) {
    return ''
  }

  const lastDay = new Date(Date.UTC(year, month, 0)).getUTCDate()
  return `${year}-${String(month).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`
}

export function isoDateToMonthYear(isoDate) {
  const match = /^(\d{4})-(\d{2})/.exec(isoDate || '')
  if (!match) {
    return { month: null, year: null }
  }

  return { month: Number(match[2]), year: Number(match[1]) }
}

export function formatExpiryMonth(isoDate) {
  const { month, year } = isoDateToMonthYear(isoDate)
  if (!month) {
    return '—'
  }

  return `${MONTH_LABELS[month - 1].toLowerCase()} ${year}`
}

export function formatDateTime(value) {
  if (!value) {
    return ''
  }

  return new Date(value).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

export function formatQuantity(value) {
  const numeric = Number(value)
  if (Number.isNaN(numeric)) {
    return value ?? ''
  }

  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 }).format(numeric)
}
