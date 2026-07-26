import { afterEach, describe, expect, it, vi } from 'vitest'

import { qualityApi } from './qualityApi'

const report = {
  id: '00000000-0000-4000-8000-000000000001',
  trigger: 'manual',
  score: 96,
  issue_count: 1,
  error_count: 0,
  warning_count: 1,
  info_count: 0,
  started_at: '2026-07-22T12:00:00Z',
  completed_at: '2026-07-22T12:00:01Z',
  issues: []
}

afterEach(() => vi.unstubAllGlobals())

describe('quality API', () => {
  it('loads the latest report through the local read endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(report), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    }))
    vi.stubGlobal('fetch', fetchMock)

    expect((await qualityApi.latest()).score).toBe(96)
    expect(String(fetchMock.mock.calls[0]?.[0])).toBe('/api/v1/quality/latest')
  })

  it('starts manual checks only through the dedicated POST endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(report), {
      status: 201,
      headers: { 'Content-Type': 'application/json' }
    }))
    vi.stubGlobal('fetch', fetchMock)

    await qualityApi.run()

    expect(String(fetchMock.mock.calls[0]?.[0])).toBe('/api/v1/quality/run')
    expect((fetchMock.mock.calls[0]?.[1] as RequestInit).method).toBe('POST')
  })
})
