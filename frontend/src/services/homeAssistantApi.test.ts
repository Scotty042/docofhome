import { afterEach, describe, expect, it, vi } from 'vitest'

import { homeAssistantApi } from './homeAssistantApi'

afterEach(() => vi.unstubAllGlobals())

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' }
  })
}

describe('Home Assistant API', () => {
  it('reads and atomically replaces the local selection', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({
        mode: 'all', entity_ids: [], selected_count: 0, updated_at: null
      }))
      .mockResolvedValueOnce(jsonResponse({
        mode: 'selected', entity_ids: ['sensor.a'], selected_count: 1,
        updated_at: '2026-07-21T18:00:00Z'
      }))
    vi.stubGlobal('fetch', fetchMock)

    await homeAssistantApi.selection()
    await homeAssistantApi.updateSelection({ mode: 'selected', entity_ids: ['sensor.a'] })

    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/home-assistant/selection')
    const init = fetchMock.mock.calls[1][1] as RequestInit
    expect(init.method).toBe('PUT')
    expect(JSON.parse(init.body as string)).toEqual({
      mode: 'selected', entity_ids: ['sensor.a']
    })
  })

  it('loads every entity page with all-selection scope and refreshes only once', async () => {
    const firstItems = Array.from({ length: 1000 }, (_, index) => ({ entity_id: `sensor.${index}` }))
    const secondItems = [{ entity_id: 'sensor.1000' }]
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ items: firstItems, total: 1001 }))
      .mockResolvedValueOnce(jsonResponse({ items: secondItems, total: 1001 }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await homeAssistantApi.allEntities({
      selection_scope: 'all',
      refresh: true
    })

    expect(result).toHaveLength(1001)
    expect(String(fetchMock.mock.calls[0][0])).toContain('selection_scope=all')
    expect(String(fetchMock.mock.calls[0][0])).toContain('refresh=true')
    expect(String(fetchMock.mock.calls[0][0])).toContain('offset=0')
    expect(String(fetchMock.mock.calls[1][0])).toContain('offset=1000')
    expect(String(fetchMock.mock.calls[1][0])).not.toContain('refresh=true')
  })
  it('loads asset-specific links and current Home Assistant properties', async () => {
    const payload = {
      asset_id: 'asset-1',
      device_links: [],
      entity_links: [],
      devices: [],
      entities: [],
      missing_device_ids: [],
      missing_entity_ids: [],
      warning: null,
      refreshed_at: null
    }
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ items: [] }))
      .mockResolvedValueOnce(jsonResponse(payload))
    vi.stubGlobal('fetch', fetchMock)

    await homeAssistantApi.links('asset-1')
    await homeAssistantApi.assetBindings('asset-1', true)

    expect(fetchMock.mock.calls[0][0]).toBe(
      '/api/v1/home-assistant/links?asset_id=asset-1'
    )
    expect(fetchMock.mock.calls[1][0]).toBe(
      '/api/v1/home-assistant/assets/asset-1?refresh=true'
    )
  })

})
