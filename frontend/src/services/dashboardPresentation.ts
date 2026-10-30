import type { ConsumptionReadingReminder } from '../types/consumption'

export function groupReadingReminders(rows: ConsumptionReadingReminder[]) {
  const groups = new Map<string, { key: string; dueAt: string; days: number; status: ConsumptionReadingReminder['status']; items: ConsumptionReadingReminder[] }>()
  for (const row of rows) {
    // Use the supplied instant, not a machine-dependent date conversion. Distinct deadlines
    // and urgency states must never be merged into an innocuous "upcoming" summary.
    const key = `${row.due_at}|${row.status}`
    const group = groups.get(key) ?? { key, dueAt: row.due_at, days: row.days_remaining, status: row.status, items: [] }
    if (!group.items.some(item => item.meter_id === row.meter_id)) group.items.push(row)
    group.days = Math.min(group.days, row.days_remaining)
    groups.set(key, group)
  }
  return [...groups.values()].sort((a, b) => a.days - b.days)
}
