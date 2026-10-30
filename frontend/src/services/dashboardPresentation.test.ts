import { describe, expect, it } from 'vitest'
import { groupReadingReminders } from './dashboardPresentation'
import type { ConsumptionReadingReminder } from '../types/consumption'
const reminder = (id: string, days: number, status: ConsumptionReadingReminder['status'], date = '2026-10-31T00:00:00+01:00'): ConsumptionReadingReminder => ({ meter_id: id, meter_name: id, unit: 'm³', due_at: date, days_remaining: days, status })
describe('grouped dashboard reminders', () => {
  it('keeps different meters with the same name and groups only the same deadline and urgency', () => {
    const rows = [reminder('a', 2, 'upcoming'), reminder('b', 2, 'upcoming')].map(item => ({ ...item, meter_name: 'Wasser' }))
    const result = groupReadingReminders(rows)
    expect(result).toHaveLength(1)
    expect(result[0].items.map(item => item.meter_id)).toEqual(['a', 'b'])
  })
  it('keeps overdue and today visible before upcoming deadlines and deduplicates repeated meter IDs', () => {
    const rows = [reminder('future', 2, 'upcoming'), reminder('old', -1, 'overdue', '2026-10-28T00:00:00+01:00'), reminder('today', 0, 'today'), reminder('future', 2, 'upcoming')]
    expect(groupReadingReminders(rows).map(group => [group.status, group.items.length])).toEqual([['overdue', 1], ['today', 1], ['upcoming', 1]])
  })
})
