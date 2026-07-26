import type { ConsumptionSeries } from '../types/consumption'

export function consumptionSeriesMax(series: ConsumptionSeries): number {
  return Math.max(1, ...series.points.map((point) => point.result.value ?? 0))
}
