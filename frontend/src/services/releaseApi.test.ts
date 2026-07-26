import { afterEach, describe, expect, it, vi } from 'vitest'

import { releaseApi } from './releaseApi'

afterEach(() => vi.unstubAllGlobals())

describe('release APIs', () => {
  it('previews switch ports before generation', async () => {
    const body = {
      device_id: 'device-1', existing_names: [], create_names: ['1', '2'],
      unchanged_names: [], requested_total: 2
    }
    const fetchMock = vi.fn().mockImplementation(async () => new Response(
      JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } }
    ))
    vi.stubGlobal('fetch', fetchMock)
    const groups = [{
      group: 'copper' as const, count: 2, scheme: 'numeric' as const,
      start: 1, speed_mbps: 1000, poe_capable: true
    }]

    await releaseApi.previewPorts('device-1', groups)
    await releaseApi.generatePorts('device-1', groups)

    expect(String(fetchMock.mock.calls[0]?.[0])).toContain('/ports/preview')
    expect(String(fetchMock.mock.calls[1]?.[0])).toContain('/ports/generate')
    expect(JSON.parse(String((fetchMock.mock.calls[0]?.[1] as RequestInit).body))).toEqual({ groups })
  })

  it('keeps import preview read-only and passes an explicit conflict strategy', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        format: 'DocOfHome JSON', export_version: '1.0', record_counts: {},
        conflicts: [], warnings: [], writable: false
      }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        created: 0, skipped: 0, conflicts: 0, modules: [], rolled_back: false
      }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    vi.stubGlobal('fetch', fetchMock)
    const file = new File(['{}'], 'export.json', { type: 'application/json' })

    expect((await releaseApi.previewImport(file)).writable).toBe(false)
    await releaseApi.applyImport(file, 'skip')

    expect(String(fetchMock.mock.calls[1]?.[0])).toContain('strategy=skip')
    expect((fetchMock.mock.calls[0]?.[1] as RequestInit).body).toBeInstanceOf(FormData)
  })
})
