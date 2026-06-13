import { describe, it, expect } from 'vitest'
import { medicineCountLabel } from './medicineCount'

describe('medicineCountLabel', () => {
  it('shows the total with the "всего" prefix when no filters are active', () => {
    expect(medicineCountLabel(12, false)).toBe('Всего 12 лекарств')
  })

  it('shows the found count with the "найдено" prefix when filters are active', () => {
    expect(medicineCountLabel(3, true)).toBe('Найдено 3 лекарства')
  })

  it('uses the singular form for counts ending in 1 (but not 11)', () => {
    expect(medicineCountLabel(1, false)).toBe('Всего 1 лекарство')
    expect(medicineCountLabel(21, false)).toBe('Всего 21 лекарство')
    expect(medicineCountLabel(11, false)).toBe('Всего 11 лекарств')
  })

  it('uses the few form for counts ending in 2-4 (but not 12-14)', () => {
    expect(medicineCountLabel(2, false)).toBe('Всего 2 лекарства')
    expect(medicineCountLabel(24, false)).toBe('Всего 24 лекарства')
    expect(medicineCountLabel(13, false)).toBe('Всего 13 лекарств')
  })

  it('uses the many form for zero', () => {
    expect(medicineCountLabel(0, true)).toBe('Найдено 0 лекарств')
  })
})
