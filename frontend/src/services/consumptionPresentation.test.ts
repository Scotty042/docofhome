import { describe, expect, it } from 'vitest'

import { consumptionSeriesMax } from './consumptionPresentation'
import type { ConsumptionSeries } from '../types/consumption'

function series(name: string, values: Array<number | null>): ConsumptionSeries {
  return {
    key: name,
    name,
    meter_id: name,
    meter_type: 'electricity_grid',
    unit: 'kWh',
    decimals: 1,
    virtual: false,
    description: null,
    points: values.map((value, index) => ({
      label: String(index + 1),
      period_start: `2026-${String(index + 1).padStart(2, '0')}-01T00:00:00Z`,
      period_end: `2026-${String(index + 2).padStart(2, '0')}-01T00:00:00Z`,
      result: { value, estimated: false, incomplete: false, reset_detected: false }
    }))
  }
}

describe('consumption chart scaling', () => {
  it('calculates the scale independently for every meter series', () => {
    expect(consumptionSeriesMax(series('Gas', [5, 10, 8]))).toBe(10)
    expect(consumptionSeriesMax(series('Strom', [120, 260, 180]))).toBe(260)
  })

  it('keeps empty series renderable', () => {
    expect(consumptionSeriesMax(series('Leer', [null, null]))).toBe(1)
  })
})
