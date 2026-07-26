import { afterEach, describe, expect, it, vi } from 'vitest'

import { immichApi } from './immichApi'

afterEach(() => vi.unstubAllGlobals())

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' }
  })
}

describe('Immich API transport', () => {
  it('loads read-only albums through docofhome', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({
      items: [{
        immich_album_id: 'album-id',
        album_name: 'Elektro',
        asset_count: 7,
        thumbnail_asset_id: null,
        thumbnail_url: null,
        start_date: null,
        end_date: null
      }]
    }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await immichApi.albums()

    expect(result.items[0].album_name).toBe('Elektro')
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/immich/albums')
    expect(JSON.stringify(fetchMock.mock.calls)).not.toContain('x-api-key')
  })

  it('browses through docofhome with paging and filename search', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({
      items: [], total: 0, page: 2, page_size: 24, pages: 0
    }))
    vi.stubGlobal('fetch', fetchMock)

    await immichApi.browse({ page: 2, page_size: 24, search: 'panel photo' })

    const url = String(fetchMock.mock.calls[0][0])
    expect(url).toContain('/api/v1/immich/assets?')
    expect(url).toContain('page=2')
    expect(url).toContain('search=panel+photo')
    expect(url).not.toContain('apiKey')
    expect(url).not.toContain('x-api-key')
  })

  it('serializes album, favorite and taken-date filters only to the local API', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({
      items: [], total: 0, page: 1, page_size: 36, pages: 0
    }))
    vi.stubGlobal('fetch', fetchMock)

    await immichApi.browse({
      album_id: '00000000-0000-0000-0000-000000000001',
      favorite_only: true,
      taken_after: '2026-01-01T00:00:00',
      taken_before: '2026-01-31T23:59:59.999'
    })

    const url = String(fetchMock.mock.calls[0][0])
    expect(url).toContain('album_id=00000000-0000-0000-0000-000000000001')
    expect(url).toContain('favorite_only=true')
    expect(url).toContain('taken_after=2026-01-01T00%3A00%3A00')
    expect(url).toContain('taken_before=2026-01-31T23%3A59%3A59.999')
    expect(url).not.toContain('immich.test')
    expect(url).not.toContain('secret')
  })

  it('creates, lists and removes local links without external credentials', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ items: [] }))
      .mockResolvedValueOnce(jsonResponse({ id: 'link-id' }, 201))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetchMock)

    await immichApi.links('asset-id')
    await immichApi.createLink('asset-id', 'immich-id')
    await immichApi.removeLink('link-id')

    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/immich/links?asset_id=asset-id')
    expect(JSON.parse(fetchMock.mock.calls[1][1].body as string)).toEqual({
      asset_id: 'asset-id', immich_asset_id: 'immich-id'
    })
    expect(fetchMock.mock.calls[2][1].method).toBe('DELETE')
    expect(JSON.stringify(fetchMock.mock.calls)).not.toContain('secret')
  })
})
