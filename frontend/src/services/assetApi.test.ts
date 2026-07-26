import { afterEach, describe, expect, it, vi } from 'vitest'

import { assetApi, AssetApiError } from './assetApi'
import { createEmptyAsset } from '../types/assets'

afterEach(() => vi.unstubAllGlobals())

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' }
  })
}

describe('asset API', () => {
  it('serializes paging, search, sorting and filters', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({
      items: [], total: 0, page: 2, page_size: 10, pages: 0
    }))
    vi.stubGlobal('fetch', fetchMock)

    await assetApi.list({
      page: 2,
      page_size: 10,
      search: 'office pc',
      sort_by: 'name',
      sort_order: 'desc',
      status: 'active',
      location_id: 'location-id'
    })

    const url = String(fetchMock.mock.calls[0][0])
    expect(url).toContain('/api/v1/assets?')
    expect(url).toContain('search=office+pc')
    expect(url).toContain('status=active')
    expect(url).toContain('location_id=location-id')
  })

  it('sends the complete editor payload on create', async () => {
    const payload = createEmptyAsset()
    payload.name = 'Test asset'
    payload.asset_type_id = 'type-id'
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ id: 'asset-id' }, 201))
    vi.stubGlobal('fetch', fetchMock)

    await assetApi.create(payload)

    const init = fetchMock.mock.calls[0][1] as RequestInit
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body as string)).toEqual(payload)
  })

  it('creates an asset type through the master data API', async () => {
    const payload = { name: 'Server', description: 'Physical host', icon: 'mdi-server', module_width: null }
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({
      id: 'type-id', code_prefix: 'SERV', ...payload
    }, 201))
    vi.stubGlobal('fetch', fetchMock)

    await assetApi.createAssetType(payload)

    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/asset-types')
    const init = fetchMock.mock.calls[0][1] as RequestInit
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body as string)).toEqual(payload)
  })

  it('loads every master data page instead of stopping after 100 records', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({
        items: [{ id: 'type-1', name: 'A' }], total: 2, page: 1, page_size: 100, pages: 2
      }))
      .mockResolvedValueOnce(jsonResponse({
        items: [{ id: 'type-2', name: 'B' }], total: 2, page: 2, page_size: 100, pages: 2
      }))
    vi.stubGlobal('fetch', fetchMock)

    const items = await assetApi.allAssetTypes(true)

    expect(items.map((item) => item.id)).toEqual(['type-1', 'type-2'])
    expect(String(fetchMock.mock.calls[0][0])).toContain('page=1')
    expect(String(fetchMock.mock.calls[0][0])).toContain('include_deleted=true')
    expect(String(fetchMock.mock.calls[1][0])).toContain('page=2')
  })

  it('handles successful soft deletion without parsing an empty response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status: 204 })))
    await expect(assetApi.remove('asset-id')).resolves.toBeUndefined()
  })

  it('creates a replacement through the immutable history workflow', async () => {
    const payload = createEmptyAsset()
    payload.name = 'Replacement'
    payload.asset_type_id = 'type-id'
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({
      archived: { id: 'old-id' },
      replacement: { id: 'new-id' },
      relationship: { id: 'relationship-id', relationship_type: 'replaced_by' }
    }, 201))
    vi.stubGlobal('fetch', fetchMock)

    await assetApi.replace('old-id', payload, ' Hardware refresh ')

    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/assets/old-id/replacement')
    const init = fetchMock.mock.calls[0][1] as RequestInit
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body as string)).toEqual({
      replacement: payload,
      reason: 'Hardware refresh'
    })
  })

  it('surfaces backend validation errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(
      { detail: 'Asset type does not exist' }, 422
    )))

    await expect(assetApi.create(createEmptyAsset())).rejects.toEqual(
      new AssetApiError('Asset type does not exist', 422)
    )
  })
})
