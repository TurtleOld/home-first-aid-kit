import { describe, it, expect } from 'vitest'
import {
  monthYearToIsoDate,
  isoDateToMonthYear,
  formatExpiryMonth,
  formatDateTime,
  formatQuantity
} from './expiry'

describe('monthYearToIsoDate', () => {
  it('returns the last day of the given month', () => {
    expect(monthYearToIsoDate(2, 2026)).toBe('2026-02-28')
    expect(monthYearToIsoDate(12, 2026)).toBe('2026-12-31')
  })

  it('returns the last day of a leap-year February', () => {
    expect(monthYearToIsoDate(2, 2028)).toBe('2028-02-29')
  })

  it('returns an empty string when month or year is missing', () => {
    expect(monthYearToIsoDate(null, 2026)).toBe('')
    expect(monthYearToIsoDate(5, null)).toBe('')
  })
})

describe('isoDateToMonthYear', () => {
  it('parses month and year from an ISO date', () => {
    expect(isoDateToMonthYear('2026-07-31')).toEqual({ month: 7, year: 2026 })
  })

  it('returns nulls for an empty or invalid value', () => {
    expect(isoDateToMonthYear('')).toEqual({ month: null, year: null })
    expect(isoDateToMonthYear('not-a-date')).toEqual({ month: null, year: null })
  })
})

describe('formatExpiryMonth', () => {
  it('formats a known date as a lowercase month name and year', () => {
    expect(formatExpiryMonth('2026-07-31')).toBe('июль 2026')
  })

  it('returns a dash for an empty value', () => {
    expect(formatExpiryMonth('')).toBe('—')
  })
})

describe('formatDateTime', () => {
  it('returns an empty string for falsy values', () => {
    expect(formatDateTime(null)).toBe('')
    expect(formatDateTime('')).toBe('')
  })

  it('formats a date-time value', () => {
    const result = formatDateTime('2026-06-12T10:30:00Z')
    expect(result).toMatch(/\d{2}\.\d{2}\.\d{4}/)
  })
})

describe('formatQuantity', () => {
  it('formats numeric values with ru-RU separators', () => {
    expect(formatQuantity(1000)).toBe('1 000')
    expect(formatQuantity(2.5)).toBe('2,5')
  })

  it('returns the original value when it is not a number', () => {
    expect(formatQuantity('abc')).toBe('abc')
    expect(formatQuantity(undefined)).toBe('')
  })
})
