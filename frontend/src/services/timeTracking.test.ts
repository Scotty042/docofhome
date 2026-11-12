import { describe, expect, it } from 'vitest'
import { intervalSeconds, formatDuration } from './timeTracking'

describe('ticket and daily durations', () => {
  it('adds resumed slots and excludes the intervening pause', () => {
    const first = intervalSeconds(8*3600, 9*3600, 0, 86400)
    const second = intervalSeconds(10.5*3600, 11.25*3600, 0, 86400)
    expect(formatDuration(first + second)).toBe('01:45:00')
  })
  it('splits midnight intervals without double counting', () => {
    const firstDay = intervalSeconds(23*3600, 25*3600, 0, 86400)
    const nextDay = intervalSeconds(23*3600, 25*3600, 86400, 172800)
    expect(firstDay).toBe(3600)
    expect(nextDay).toBe(3600)
    expect(intervalSeconds(1, 2, 86400, 172800)).toBe(0)
  })
  it('retains long totals and displays seconds without rounding up', () => {
    expect(formatDuration(90000.9)).toBe('25:00:00')
  })
})

import { quickRange, rangeBounds, localDateTime } from './timeTracking'
describe('history ranges', () => {
  const today = new Date(2026, 10, 12, 14, 30)
  it('defaults to 30 calendar days including today', () => {
    expect(quickRange('30', today)).toEqual(['2026-10-14', '2026-11-12'])
    expect(quickRange('7', today)).toEqual(['2026-11-06', '2026-11-12'])
    expect(quickRange('today', today)).toEqual(['2026-11-12', '2026-11-12'])
    expect(quickRange('yesterday', today)).toEqual(['2026-11-11', '2026-11-11'])
  })
  it('handles month and year boundaries and leap years', () => {
    expect(quickRange('month', today)).toEqual(['2026-11-01', '2026-11-12'])
    expect(quickRange('last-month', new Date(2024, 2, 31))).toEqual(['2024-02-01', '2024-02-29'])
    expect(quickRange('last-year', today)).toEqual(['2025-01-01', '2025-12-31'])
    expect(quickRange('year', today)).toEqual(['2026-01-01', '2026-11-12'])
  })
  it('includes the complete final day and rejects inverted or empty ranges', () => {
    const bounds = rangeBounds('2026-11-11', '2026-11-12')!
    expect(new Date(bounds[1]*1000).getDate()).toBe(13)
    expect(new Date(bounds[1]*1000).getHours()).toBe(0)
    expect(rangeBounds('2026-11-12', '2026-11-11')).toBeNull()
    expect(rangeBounds('', '2026-11-12')).toBeNull()
    expect(localDateTime(new Date(2026, 10, 12, 8, 5, 3).getTime()/1000)).toBe('2026-11-12T08:05:03')
  })
})
