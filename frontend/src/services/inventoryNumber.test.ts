import { describe, expect, it } from 'vitest'

import { incrementInventoryNumber } from './inventoryNumber'

describe('inventory number increment', () => {
  it('starts empty inventory numbers at one', () => {
    expect(incrementInventoryNumber(null)).toBe('1')
  })

  it('preserves prefixes and leading zeroes', () => {
    expect(incrementInventoryNumber('INV-009')).toBe('INV-010')
    expect(incrementInventoryNumber('009')).toBe('010')
  })

  it('adds a numeric suffix when none exists', () => {
    expect(incrementInventoryNumber('Inventar')).toBe('Inventar-1')
    expect(incrementInventoryNumber('INV-')).toBe('INV-1')
  })
})
