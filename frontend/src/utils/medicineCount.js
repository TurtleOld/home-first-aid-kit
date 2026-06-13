const MEDICINE_FORMS = ['лекарство', 'лекарства', 'лекарств']

function pluralizeMedicine(count) {
  const abs = Math.abs(count) % 100
  const tail = abs % 10
  if (abs > 10 && abs < 20) {
    return MEDICINE_FORMS[2]
  }
  if (tail > 1 && tail < 5) {
    return MEDICINE_FORMS[1]
  }
  if (tail === 1) {
    return MEDICINE_FORMS[0]
  }
  return MEDICINE_FORMS[2]
}

export function medicineCountLabel(count, hasFilters) {
  const prefix = hasFilters ? 'Найдено' : 'Всего'
  return `${prefix} ${count} ${pluralizeMedicine(count)}`
}
