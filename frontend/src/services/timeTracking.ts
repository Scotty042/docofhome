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
