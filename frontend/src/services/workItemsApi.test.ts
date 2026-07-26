import { afterEach, describe, expect, it, vi } from 'vitest'

import { workItemsApi } from './workItemsApi'

const item = {
  id: '00000000-0000-4000-8000-000000000001',
  item_type: 'maintenance',
  title: 'Filter wechseln',
  description: null,
  target_type: 'asset',
  target_id: '00000000-0000-4000-8000-000000000002',
  target_label: 'Wärmepumpe',
  target_route: '/assets/00000000-0000-4000-8000-000000000002',
  due_at: '2026-08-01T10:00:00Z',
  recurrence_days: 180,
  priority: 'normal',
  status: 'open',
  overdue: false,
  completed_at: null,
  created_at: '2026-07-22T12:00:00Z',
  updated_at: '2026-07-22T12:00:00Z'
}

afterEach(() => vi.unstubAllGlobals())

describe('work items API', () => {
  it('serializes target-bound filters without external URLs', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify([item]), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    }))
    vi.stubGlobal('fetch', fetchMock)

    await workItemsApi.list({ targetType: 'asset', targetId: item.target_id })

    expect(String(fetchMock.mock.calls[0]?.[0])).toBe(
      `/api/v1/work-items?target_type=asset&target_id=${item.target_id}`
    )
  })

  it('completes through a dedicated local transition endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(item), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    }))
    vi.stubGlobal('fetch', fetchMock)

    await workItemsApi.complete(item.id, 'Erledigt')

    expect(String(fetchMock.mock.calls[0]?.[0])).toBe(`/api/v1/work-items/${item.id}/complete`)
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit
    expect(init.method).toBe('POST')
    expect(JSON.parse(String(init.body))).toEqual({ note: 'Erledigt' })
  })
})
