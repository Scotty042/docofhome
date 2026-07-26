import { afterEach, describe, expect, it, vi } from 'vitest'

import { networkApi } from './networkApi'

const response = (body: unknown, status = 200) => new Response(
  status === 204 ? null : JSON.stringify(body),
  { status, headers: { 'Content-Type': 'application/json' } }
)

afterEach(() => vi.unstubAllGlobals())

describe('networkApi', () => {
  it('uses the local v1 API and serializes device filters', async () => {
    const fetchMock = vi.fn().mockResolvedValue(response([]))
    vi.stubGlobal('fetch', fetchMock)

    await networkApi.devices({ search: 'switch', role: 'switch', includeArchived: false })

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/network/devices?search=switch&role=switch&include_archived=false',
      expect.objectContaining({ headers: expect.objectContaining({ 'Content-Type': 'application/json' }) })
    )
  })

  it('creates a connection with an explicit JSON payload', async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({ id: 'connection-1' }, 201))
    vi.stubGlobal('fetch', fetchMock)
    const payload = {
      source_interface_id: 'a',
      target_interface_id: 'b',
      connection_type: 'physical' as const,
      status: 'active' as const,
      cable_type: 'Cat 6A',
      cable_label: null,
      description: null
    }

    await networkApi.createConnection(payload)

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/network/connections',
      expect.objectContaining({ method: 'POST', body: JSON.stringify(payload) })
    )
  })
})
