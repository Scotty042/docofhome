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

import { groupByDay, activitiesToday } from './timeTracking'
describe('daily history and resuming today', () => {
  const at = (value: string) => new Date(value).getTime()/1000
  const interval = (ticket: string, start: string, end: string | null, info = '') => ({
    ticket, started_at: at(start), ended_at: end ? at(end) : null, info
  })
  it('groups newest days first, keeps multiple runs and adds their daily durations', () => {
    const rows = [
      interval('A', '2026-11-11T08:00:00', '2026-11-11T09:00:00'),
      interval('B', '2026-11-12T08:00:00', '2026-11-12T09:00:00'),
      interval('A', '2026-11-12T10:00:00', '2026-11-12T10:30:00')
    ]
    const days = groupByDay(rows, rangeBounds('2026-11-11', '2026-11-12'), at('2026-11-12T12:00:00'))
    expect(days.map(day => day.day)).toEqual(['2026-11-12', '2026-11-11'])
    expect(days.map(day => day.total)).toEqual([5400, 3600])
    expect(days[0]!.slots.map(slot => slot.interval.ticket)).toEqual(['A', 'B'])
  })
  it('splits midnight runs, clips selected days and preserves the source interval for editing', () => {
    const row = interval('A', '2026-11-11T23:00:00', '2026-11-12T01:00:00')
    const days = groupByDay([row], rangeBounds('2026-11-11', '2026-11-12'), at('2026-11-12T12:00:00'))
    expect(days.map(day => day.total)).toEqual([3600, 3600])
    expect(days[0]!.slots[0]!.interval).toBe(row)
    expect(groupByDay([row], rangeBounds('2026-11-12', '2026-11-12'), at('2026-11-12T12:00:00'))[0]!.total).toBe(3600)
    expect(groupByDay([row], null, at('2026-11-12T12:00:00'))).toEqual([])
  })
  it('shows only today’s activities once, using the most recent run, independent of history filter', () => {
    const rows = [
      interval('old', '2026-11-11T08:00:00', '2026-11-11T09:00:00'),
      interval('midnight-end', '2026-11-11T23:00:00', '2026-11-12T00:00:00'),
      interval('night', '2026-11-11T23:30:00', null),
      interval('today', '2026-11-12T08:00:00', '2026-11-12T09:00:00', 'old info'),
      interval('today', '2026-11-12T10:00:00', '2026-11-12T11:00:00', 'new info')
    ]
    const recent = activitiesToday(rows, at('2026-11-12T12:00:00'))
    expect(recent.map(row => row.ticket)).toEqual(['today', 'night'])
    expect(recent[0]!.info).toBe('new info')
    expect(activitiesToday(rows, at('2026-11-13T12:00:00')).map(row => row.ticket)).toEqual(['night'])
  })
  it('uses calendar midnights on daylight saving transitions', () => {
    for (const [day, next] of [['2026-03-29', '2026-03-30'], ['2026-10-25', '2026-10-26']]) {
      const row = interval('DST', `${day}T00:00:00`, `${next}T00:00:00`)
      const days = groupByDay([row], rangeBounds(day!, day!), at(`${next}T12:00:00`))
      expect(days).toHaveLength(1)
      expect(days[0]!.total).toBe(at(`${next}T00:00:00`) - at(`${day}T00:00:00`))
    }
  })
})

it('counts overlapping activity durations independently in daily totals', () => {
  const at = (value: string) => new Date(value).getTime()/1000
  const days = groupByDay([
    { ticket: 'A', started_at: at('2026-11-12T08:00:00'), ended_at: at('2026-11-12T09:30:00') },
    { ticket: 'B', started_at: at('2026-11-12T08:30:00'), ended_at: at('2026-11-12T10:00:00') }
  ], rangeBounds('2026-11-12', '2026-11-12'), at('2026-11-12T12:00:00'))
  expect(days).toHaveLength(1)
  expect(days[0]!.slots).toHaveLength(2)
  expect(formatDuration(days[0]!.total)).toBe('03:00:00')
})

import { customerSections, sortHistory, summarizeActivities } from './timeTracking'
describe('customer grouping and sorting', () => {
  const slots = [
    { interval: { id:'a', ticket:'T-10', customer:'KD', info:'A', bcs:false, running:false, completed:true, started_at:100, ended_at:200 }, start:100, end:200, seconds:100 },
    { interval: { id:'b', ticket:'T-2', customer:'KD', info:'B', bcs:true, running:false, completed:false, started_at:300, ended_at:350 }, start:300, end:350, seconds:50 },
    { interval: { id:'c', ticket:'T-3', customer:'KD2', info:'C', bcs:false, running:false, completed:true, started_at:400, ended_at:600 }, start:400, end:600, seconds:200 }
  ]
  it('sorts numerically by ticket and reverses direction without changing source rows', () => {
    expect(sortHistory(slots,'ticket','asc').map(s=>s.interval.id)).toEqual(['b','c','a'])
    expect(sortHistory(slots,'ticket','desc').map(s=>s.interval.id)).toEqual(['a','c','b'])
    expect(slots.map(s=>s.interval.id)).toEqual(['a','b','c'])
    expect(sortHistory(slots,'seconds','asc').map(s=>s.interval.id)).toEqual(['b','a','c'])
    expect(sortHistory(slots,'bcs','desc')[0]!.interval.id).toBe('b')
    expect(sortHistory(slots,'end','desc')[0]!.interval.id).toBe('c')
  })
  it('groups per customer with correct totals and sorts inside each group', () => {
    const sections = customerSections(slots,true,'ticket','asc')
    expect(sections.map(g=>g.customer)).toEqual(['KD','KD2'])
    expect(sections.map(g=>g.total)).toEqual([150,200])
    expect(sections[0]!.slots.map(s=>s.interval.id)).toEqual(['b','a'])
    expect(customerSections(slots,false,'ticket','asc')).toHaveLength(1)
  })
  it('keeps days separated when applying customer grouping and sorting', () => {
    const at = (v:string)=>new Date(v).getTime()/1000
    const days = groupByDay([
      {...slots[0]!.interval, started_at:at('2026-11-16T08:00:00'), ended_at:at('2026-11-16T09:00:00')},
      {...slots[1]!.interval, started_at:at('2026-11-17T08:00:00'), ended_at:at('2026-11-17T09:00:00')}
    ],rangeBounds('2026-11-16','2026-11-17'),at('2026-11-17T12:00:00'))
    expect(days.map(d=>d.day)).toEqual(['2026-11-17','2026-11-16'])
    expect(days.map(d=>customerSections(d.slots,true,'ticket','asc')[0]!.slots[0]!.interval.id)).toEqual(['b','a'])
  })
  it('includes the customer in summaries and keeps identical tickets for different customers separate', () => {
    const rows = [slots[0]!.interval, {...slots[1]!.interval,ticket:'T-10'}, {...slots[2]!.interval,ticket:'T-10'}]
    const totals = summarizeActivities(rows,[0,1000],1000)
    expect(totals.map(g=>[g.ticket,g.customer,g.total])).toEqual([['T-10','KD',150],['T-10','KD2',200]])
    expect(new Set(totals.map(g=>g.key)).size).toBe(2)
  })
})
