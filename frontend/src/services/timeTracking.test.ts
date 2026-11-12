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
