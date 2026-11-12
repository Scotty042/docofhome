export function intervalSeconds(start: number, end: number, dayStart: number, dayEnd: number): number {
  return Math.max(0, Math.min(end, dayEnd) - Math.max(start, dayStart))
}
export function formatDuration(value: number): string {
  const n = Math.floor(Math.max(0, value))
  return `${String(Math.floor(n/3600)).padStart(2,'0')}:${String(Math.floor(n/60)%60).padStart(2,'0')}:${String(n%60).padStart(2,'0')}`
}

export const rangeOptions = [
  { title: 'Heute', value: 'today' }, { title: 'Gestern', value: 'yesterday' },
  { title: 'Letzte 7 Tage', value: '7' }, { title: 'Letzte 30 Tage', value: '30' },
  { title: 'Letzte 90 Tage', value: '90' }, { title: 'Letzte 365 Tage', value: '365' },
  { title: 'Dieser Monat', value: 'month' }, { title: 'Letzter Monat', value: 'last-month' },
  { title: 'Dieses Jahr', value: 'year' }, { title: 'Letztes Jahr', value: 'last-year' },
  { title: 'Eigener Zeitraum', value: 'custom' }
]
export function localDay(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}
export function quickRange(value: string, today = new Date()): [string, string] {
  const end = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  const start = new Date(end)
  if (/^\d+$/.test(value)) start.setDate(start.getDate() - (Number(value) - 1))
  if (value === 'yesterday') { start.setDate(start.getDate()-1); end.setDate(end.getDate()-1) }
  if (value === 'month') start.setDate(1)
  if (value === 'last-month') { start.setMonth(start.getMonth(), 1); start.setMonth(start.getMonth()-1); end.setDate(0) }
  if (value === 'year') start.setMonth(0, 1)
  if (value === 'last-year') { start.setFullYear(start.getFullYear()-1, 0, 1); end.setMonth(0, 0) }
  return [localDay(start), localDay(end)]
}
export function rangeBounds(from: string, to: string): [number, number] | null {
  const start = new Date(`${from}T00:00:00`), end = new Date(`${to}T00:00:00`)
  if (!from || !to || !Number.isFinite(start.getTime()) || !Number.isFinite(end.getTime()) || start > end) return null
  end.setDate(end.getDate()+1)
  return [start.getTime()/1000, end.getTime()/1000]
}
export function localDateTime(seconds: number): string {
  const d = new Date(seconds*1000)
  return `${localDay(d)}T${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}:${String(d.getSeconds()).padStart(2,'0')}`
}

export interface TimedActivity { ticket: string; started_at: number; ended_at: number | null }
export interface DaySlice<T> { interval: T; start: number; end: number; seconds: number }
export interface ActivityDay<T> { day: string; start: number; end: number; total: number; slots: DaySlice<T>[] }

export function groupByDay<T extends TimedActivity>(
  intervals: readonly T[], bounds: [number, number] | null, now: number
): ActivityDay<T>[] {
  if (!bounds) return []
  const days = new Map<string, ActivityDay<T>>()
  for (const interval of intervals) {
    const start = Math.max(interval.started_at, bounds[0])
    const end = Math.min(interval.ended_at ?? now, bounds[1])
    if (end <= start) continue
    const date = new Date(start * 1000)
    date.setHours(0, 0, 0, 0)
    while (date.getTime() / 1000 < end) {
      const dayStart = date.getTime() / 1000, key = localDay(date)
      date.setDate(date.getDate() + 1)
      const dayEnd = date.getTime() / 1000
      const sliceStart = Math.max(start, dayStart), sliceEnd = Math.min(end, dayEnd)
      const group = days.get(key) ?? { day: key, start: dayStart, end: dayEnd, total: 0, slots: [] }
      const seconds = sliceEnd - sliceStart
      group.total += seconds
      group.slots.push({ interval, start: sliceStart, end: sliceEnd, seconds })
      days.set(key, group)
    }
  }
  return [...days.values()].sort((a, b) => b.day.localeCompare(a.day)).map(day => ({
    ...day, slots: day.slots.sort((a, b) => b.start - a.start)
  }))
}

export function activitiesToday<T extends TimedActivity>(intervals: readonly T[], now: number): T[] {
  const today = localDay(new Date(now * 1000))
  const bounds = rangeBounds(today, today)!
  const result = new Map<string, T>()
  for (const interval of [...intervals].sort((a, b) => b.started_at - a.started_at)) {
    if (interval.started_at < bounds[1] && (interval.ended_at ?? now) > bounds[0]
        && !result.has(interval.ticket)) result.set(interval.ticket, interval)
  }
  return [...result.values()]
}
