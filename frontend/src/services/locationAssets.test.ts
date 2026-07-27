import { afterEach, describe, expect, it, vi } from 'vitest'

import { loadDirectAssetPage } from './locationAssets'
import type { Asset } from '../types/assets'

afterEach(() => vi.unstubAllGlobals())

function jsonResponse(body: unknown) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' }
  })
}

function asset(index: number): Asset {
  return {
    id: `asset-${index}`,
    name: `Asset ${String(index).padStart(3, '0')}`,
    jarvis_code: `AST-${String(index).padStart(5, '0')}`,
    description: null,
    asset_type_id: 'type-id',
    product_id: null,
    location_id: 'location-id',
    serial_number: null,
    inventory_number: null,
    module_width: null,
    effective_module_width: null,
    breaker_characteristic: null,
    effective_breaker_characteristic: null,
    rated_current_a: null,
    effective_rated_current_a: null,
    coil_voltage_v: null,
    effective_coil_voltage_v: null,
    coil_voltage_type: null,
    effective_coil_voltage_type: null,
    contact_count: null,
    effective_contact_count: null,
    contact_type: null,
    effective_contact_type: null,
    status: 'active',
    asset_type: { id: 'type-id', name: 'Device' },
    product: null,
    location: { id: 'location-id', name: 'Server room' },
    labels: [],
    created_at: '2026-07-20T12:00:00Z',
    updated_at: '2026-07-20T12:00:00Z',
    deleted_at: null
  }
}

describe('direct location asset pagination', () => {
  it('keeps more than 100 directly assigned assets reachable across pages', async () => {
    const allAssets = Array.from({ length: 125 }, (_, index) => asset(index + 1))
    const fetchMock = vi.fn().mockImplementation((input: RequestInfo | URL) => {
      const url = new URL(String(input), 'http://localhost')
      const page = Number(url.searchParams.get('page'))
      const pageSize = Number(url.searchParams.get('page_size'))
      const start = (page - 1) * pageSize
      return Promise.resolve(jsonResponse({
        items: allAssets.slice(start, start + pageSize),
        total: allAssets.length,
        page,
        page_size: pageSize,
        pages: Math.ceil(allAssets.length / pageSize)
      }))
    })
    vi.stubGlobal('fetch', fetchMock)

    const loadedAssets: Asset[] = []
    for (let page = 1; page <= 5; page += 1) {
      const result = await loadDirectAssetPage('location-id', page, 25)
      loadedAssets.push(...result.items)
      expect(result.total).toBe(125)
      expect(result.pages).toBe(5)
    }

    expect(loadedAssets).toHaveLength(125)
    expect(new Set(loadedAssets.map((entry) => entry.id)).size).toBe(125)
    expect(loadedAssets.at(-1)?.id).toBe('asset-125')
    expect(fetchMock).toHaveBeenCalledTimes(5)
    expect(String(fetchMock.mock.calls[4][0])).toContain(
      '/api/v1/assets?location_id=location-id&page=5&page_size=25'
    )
  })
})
