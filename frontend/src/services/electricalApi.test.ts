import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  electricalApi,
  ElectricalApiError,
  loadAllAvailableAssets,
  loadAllConnectionEndpoints
} from './electricalApi'
import type { AvailableElectricalAsset, ElectricalEndpoint, Page } from '../types/electrical'

function response(body: unknown, status = 200): Response {
  return new Response(status === 204 ? null : JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' }
  })
}

function asset(index: number): AvailableElectricalAsset {
  return {
    id: `asset-${index}`,
    name: `Asset ${index}`,
    jarvis_code: `ELE-${String(index).padStart(3, '0')}`,
    location_id: 'location-1',
    location_path: 'House / Electrical room',
    effective_module_width: null
  }
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('electrical API', () => {
  it('serializes filters and the required available-asset role', async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({
      items: [], total: 0, page: 2, page_size: 50, pages: 0
    }))
    vi.stubGlobal('fetch', fetchMock)

    await electricalApi.availableAssets({
      role: 'protective_device',
      page: 2,
      page_size: 50,
      search: 'HV 1',
      current_component_id: 'current-role'
    })

    const url = String(fetchMock.mock.calls[0]?.[0])
    expect(url).toContain('/api/v1/electrical/available-assets?')
    expect(url).toContain('role=protective_device')
    expect(url).toContain('page=2')
    expect(url).toContain('page_size=50')
    expect(url).toContain('search=HV+1')
    expect(url).toContain('current_component_id=current-role')
  })

  it('serializes nullable technical values without inventing defaults', async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({ id: 'device-1' }, 201))
    vi.stubGlobal('fetch', fetchMock)
    const payload = {
      asset_id: 'asset-1',
      distribution_id: 'distribution-1',
      area_id: null,
      device_type: 'mcb' as const,
      row_number: null,
      start_position: null,
      module_width: null,
      rated_current_a: null,
      residual_current_ma: null,
      characteristic: null,
      poles: null,
      breaking_capacity_ka: null,
      rcd_type: null,
      fuse_type: null,
      spd_type: null,
      description: null,
      notes: null
    }

    await electricalApi.createProtectiveDevice(payload)

    const init = fetchMock.mock.calls[0]?.[1] as RequestInit
    expect(JSON.parse(String(init.body))).toEqual(payload)
  })

  it('sends a scoped placement for a device-row area', async () => {
    const fetchMock = vi.fn().mockResolvedValue(response(null, 204))
    vi.stubGlobal('fetch', fetchMock)

    await electricalApi.placeDevice('distribution-1', 'device-1', {
      area_id: 'area-1',
      row_number: 2,
      start_position: 4,
      module_width: 2
    })

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      '/api/v1/electrical/distributions/distribution-1/' +
      'protective-devices/device-1/placement'
    )
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit
    expect(init.method).toBe('PUT')
    expect(JSON.parse(String(init.body))).toEqual({
      area_id: 'area-1',
      row_number: 2,
      start_position: 4,
      module_width: 2
    })
  })

  it('adds and removes an asset from one circuit', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response({ asset_id: 'asset-1' }, 201))
      .mockResolvedValueOnce(response(null, 204))
    vi.stubGlobal('fetch', fetchMock)

    await electricalApi.assignCircuitAsset('circuit-1', 'asset-1')
    await electricalApi.removeCircuitAsset('circuit-1', 'asset-1')

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      '/api/v1/electrical/circuits/circuit-1/assets'
    )
    expect(fetchMock.mock.calls[0]?.[1]).toEqual(expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ asset_id: 'asset-1' })
    }))
    expect(fetchMock.mock.calls[1]?.[0]).toBe(
      '/api/v1/electrical/circuits/circuit-1/assets/asset-1'
    )
    expect(fetchMock.mock.calls[1]?.[1]).toEqual(expect.objectContaining({
      method: 'DELETE'
    }))
  })

  it('serializes a complete supply connection payload', async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({ id: 'connection-1' }, 201))
    vi.stubGlobal('fetch', fetchMock)
    const payload = {
      source_kind: 'asset' as const,
      source_id: 'grid',
      target_kind: 'protective_device' as const,
      target_id: 'rcd',
      connection_type: 'cable' as const,
      label: 'Main supply',
      phases: ['L1', 'L2', 'L3', 'N', 'PE'] as const,
      cable_type: 'NYM-J',
      cores: 5,
      cross_section_mm2: 10,
      length_m: 12.5,
      route: 'Utility room',
      notes: null
    }

    await electricalApi.createConnection({ ...payload, phases: [...payload.phases] })

    expect(fetchMock.mock.calls[0]?.[0]).toBe('/api/v1/electrical/connections')
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit
    expect(init.method).toBe('POST')
    expect(JSON.parse(String(init.body))).toEqual(payload)
  })

  it('loads every electrical endpoint page without a hidden cutoff', async () => {
    const endpoint = (index: number): ElectricalEndpoint => ({
      key: `asset:${index}`,
      kind: 'asset',
      id: String(index),
      name: `Endpoint ${index}`,
      code: `ELE-${index}`,
      type_name: 'Electrical',
      location_name: null,
      device_type: null,
      deleted_at: null
    })
    const loadPage = vi.fn((page = 1): Promise<Page<ElectricalEndpoint>> => (
      Promise.resolve({
        items: page === 1
          ? Array.from({ length: 100 }, (_, index) => endpoint(index))
          : [endpoint(100)],
        total: 101,
        page,
        page_size: 100,
        pages: 2
      })
    ))

    const loaded = await loadAllConnectionEndpoints(loadPage)

    expect(loaded).toHaveLength(101)
    expect(loadPage).toHaveBeenCalledTimes(2)
    expect(loadPage).toHaveBeenLastCalledWith(2, 100, '')
  })

  it('loads every available-asset page beyond one hundred entries', async () => {
    const loadPage = vi.fn((query: { page?: number }): Promise<Page<AvailableElectricalAsset>> => {
      const page = query.page ?? 1
      const items = page === 1
        ? Array.from({ length: 100 }, (_, index) => asset(index))
        : Array.from({ length: 5 }, (_, index) => asset(index + 100))
      return Promise.resolve({ items, total: 105, page, page_size: 100, pages: 2 })
    })

    const loaded = await loadAllAvailableAssets(
      'distribution',
      'current-role',
      'panel',
      loadPage
    )

    expect(loaded).toHaveLength(105)
    expect(new Set(loaded.map((entry) => entry.id)).size).toBe(105)
    expect(loadPage).toHaveBeenCalledTimes(2)
    expect(loadPage).toHaveBeenLastCalledWith(expect.objectContaining({ page: 2 }))
  })

  it('reports a backend page contract that would silently drop assets', async () => {
    const loadPage = vi.fn().mockResolvedValue({
      items: [asset(1)], total: 2, page: 1, page_size: 100, pages: 1
    })
    await expect(loadAllAvailableAssets('distribution', undefined, '', loadPage)).rejects.toThrow(
      '1 von 2'
    )
  })

  it('surfaces backend conflict details', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({ detail: 'Module overlap' }, 409)))
    await expect(electricalApi.removeDistribution('distribution-1')).rejects.toEqual(
      new ElectricalApiError('Module overlap', 409)
    )
  })
})
